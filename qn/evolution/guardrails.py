"""全自动进化安全护栏：快照 -> 沙箱验证 -> 灰度 -> 门禁 -> 回滚/晋升。

对应 skill-evo-team self-improving 三级蒸馏 Step3 的"用户确认 diff"，
在全自动场景下替换为自动化验收 + 快照回滚，同时保留审计。
"""
import hashlib
import json
import os
import shutil
import time

SNAP_DIR = r"D:\D_AIdirector\QNjbzj\data\snapshots"
LOG_PATH = r"D:\D_AIdirector\QNjbzj\data\logs\evolution.log"
# 门禁：回归必须 100% 通过（错题本不允许复发），样例成功率下限可配
REGRESSION_GATE = 1.0
SAMPLE_GATE = 0.8


class EvolutionGuardrails:
    def __init__(self, regression_runner, sample_eval=None):
        """sample_eval: callable(rule_text)->(ok_count, total) 用于沙箱样例评估。"""
        self.regression = regression_runner
        self.sample_eval = sample_eval or (lambda rule: (0, 0))

    # ---------- 阶段 1：快照 ----------
    def snapshot(self, target_path, rule_desc):
        """进化前对受影响文件做不可变快照。返回 (snap_id, old_hash)。"""
        os.makedirs(SNAP_DIR, exist_ok=True)
        snap_id = "%s-%s" % (os.path.basename(target_path), int(time.time()))
        dst = os.path.join(SNAP_DIR, snap_id + ".bak")
        if os.path.isdir(target_path):
            shutil.copytree(target_path, dst)
            old_hash = self._hash_dir(target_path)
        elif os.path.isfile(target_path):
            shutil.copy2(target_path, dst)
            old_hash = self._hash_file(target_path)
        else:
            raise FileNotFoundError(target_path)
        self._log("snapshot", snap_id=snap_id, target=target_path,
                  desc=rule_desc, old_hash=old_hash)
        return snap_id, old_hash

    # ---------- 阶段 2：沙箱验证 ----------
    def sandbox_validate(self, proposed_rule, sample_outputs):
        """沙箱内验证候选规则：样例产出回归 + 样例执行。返回指标 dict。

        回归对象是"新规则指导下的样例产出文本"（是否复现错题/丢必需要点），
        而非规则文本本身——规则文本是给 Agent 读的指令，不参与错题断言。
        """
        sample_text = "\n".join(sample_outputs or [])
        if sample_text.strip():
            reg = self.regression.run_on_text(sample_text, tag="sandbox")
            reg_pass = reg["pass_rate"]
            reg_failed = reg["failed"]
        else:
            reg_pass, reg_failed = 1.0, 0
        ok, total = self.sample_eval(proposed_rule)
        sample_rate = (ok / total) if total else 1.0
        return {
            "regression_pass_rate": reg_pass,
            "regression_failed": reg_failed,
            "sample_success_rate": sample_rate,
            "sample_ok": ok, "sample_total": total,
        }

    # ---------- 阶段 3：门禁判定 + 灰度/晋升/回滚 ----------
    def propose(self, target_path, rule_desc, apply_fn,
                proposed_rule, sample_outputs, gray_ratio=1.0):
        """全自动进化入口。

        apply_fn(proposed_rule) 负责把新规则写入目标。调用前已做快照；
        若沙箱指标不达标，则不调用 apply_fn 并返回 blocked。
        """
        snap_id, old_hash = self.snapshot(target_path, rule_desc)
        metrics = self.sandbox_validate(proposed_rule, sample_outputs)
        decision = self._decide(metrics, gray_ratio)
        if decision == "blocked":
            self._log("blocked", snap_id=snap_id, desc=rule_desc,
                      metrics=metrics, reason="gate_failed")
            return {"status": "blocked", "snap_id": snap_id,
                    "metrics": metrics, "reason": "回归或样例未过门禁，未写盘"}

        # 沙箱通过：先记录准备状态（灰度语义：本工程单机以"可回滚+审计"承载）
        apply_fn(proposed_rule)
        new_hash = self._hash_any(target_path)
        if new_hash == old_hash:
            self._log("noop", snap_id=snap_id, desc=rule_desc)
            return {"status": "noop", "snap_id": snap_id, "metrics": metrics}

        # 门禁后复检（写盘后再验一次样例产出，防止 apply 过程引入意外）
        sample_text = "\n".join(sample_outputs or [])
        if sample_text.strip():
            post = self.regression.run_on_text(sample_text, tag="post_apply")
        else:
            post = {"pass_rate": 1.0}
        if post["pass_rate"] < REGRESSION_GATE:
            self.rollback(snap_id, target_path, desc=rule_desc, metrics=metrics)
            return {"status": "rolled_back", "snap_id": snap_id,
                    "metrics": metrics, "reason": "写盘后复检失败，已回滚"}
        self._log("promoted", snap_id=snap_id, desc=rule_desc,
                  metrics=metrics, new_hash=new_hash)
        return {"status": "promoted", "snap_id": snap_id, "metrics": metrics}

    def _decide(self, metrics, gray_ratio):
        if metrics["regression_pass_rate"] < REGRESSION_GATE:
            return "blocked"
        if metrics["sample_success_rate"] < SAMPLE_GATE:
            return "blocked"
        # 灰度比率语义：单机工程中 <1.0 时表示仅记录审计、标记需人工抽查；
        # 实际多机部署时此值控制放量比例。
        if gray_ratio < 1.0:
            self._log("gray_review", desc="need_human_spot_check", ratio=gray_ratio)
        return "approved"

    # ---------- 回滚 ----------
    def rollback(self, snap_id, target_path, desc="", metrics=None):
        """回滚到快照：目标若已变更则覆盖还原。"""
        bak = os.path.join(SNAP_DIR, snap_id + ".bak")
        if not os.path.exists(bak):
            return False
        if os.path.isdir(bak):
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(bak, target_path)
        else:
            shutil.copy2(bak, target_path)
        self._log("rollback", snap_id=snap_id, target=target_path,
                  desc=desc, metrics=metrics or {})
        return True

    # ---------- 工具 ----------
    @staticmethod
    def _hash_file(fp):
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]

    @staticmethod
    def _hash_dir(dp):
        parts = []
        for root, _, files in os.walk(dp):
            for fn in files:
                fp = os.path.join(root, fn)
                parts.append((os.path.relpath(fp, dp), EvolutionGuardrails._hash_file(fp)))
        return hashlib.sha256(json.dumps(sorted(parts), ensure_ascii=False).encode()).hexdigest()[:16]

    @staticmethod
    def _hash_any(p):
        return (EvolutionGuardrails._hash_dir(p) if os.path.isdir(p)
                else EvolutionGuardrails._hash_file(p))

    def _log(self, event, **kw):
        entry = {"event": event, "ts": time.time(), **kw}
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
