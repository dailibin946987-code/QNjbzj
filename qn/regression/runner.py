"""回归验证执行器：把锚点/错题本从"文档核查"变为"可执行断言"。

用例 YAML 格式（tests/cases/*.yaml）：
  - id: E-01
    title: 错题描述
    error_patterns: [ "不该出现的子串或正则(^...$)", ... ]   # 命中任一即 fail
    required_patterns: [ "必须出现的关键点", ... ]           # 缺失任一即 fail
    note: 审核要点（供报告阅读）
"""
import json
import os
import re
import time

CASE_DIR = r"D:\D_AIdirector\QNjbzj\tests\cases"
REPORT_DIR = r"D:\D_AIdirector\QNjbzj\data\logs"
_ANCHOR_DIR = r"D:\D_AIdirector\QNjbzj\data\anchors"


def _to_regex(pattern):
    """宽松转换：普通文本视作子串匹配；显式 ^...$/... 视作正则。"""
    p = pattern.strip()
    if len(p) > 2 and p[0] == "^" and p[-1] == "$":
        return re.compile(p, re.MULTILINE)
    if len(p) > 2 and p[0] == "/" and p.rfind("/") > 0:
        body, flags = p[1:p.rfind("/")], p[p.rfind("/") + 1:]
        return re.compile(body, re.MULTILINE | (re.IGNORECASE if "i" in flags else 0))
    return None


def load_cases(path=None):
    """加载 tests/cases 下全部 yaml/json 用例（用安全解析，避免额外依赖 yaml）。"""
    import json as _json
    path = path or CASE_DIR
    cases = []
    if not os.path.isdir(path):
        return cases
    for fn in sorted(os.listdir(path)):
        if fn.endswith((".yaml", ".yml", ".json")):
            cases.extend(_load_one(os.path.join(path, fn)))
    return cases


def _load_one(fp):
    # 简易 YAML 子集解析：仅支持列表元素 {k: v} 的扁平结构
    items = []
    cur = None
    with open(fp, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith("- "):
                if cur:
                    items.append(cur)
                cur = {}
                key, _, val = line[2:].partition(":")
                cur[key.strip()] = (val.strip() or "").strip("\"'")
            elif cur is not None and ":" in line:
                key, _, val = line.partition(":")
                cur[key.strip()] = (val.strip() or "").strip("\"'")
    if cur:
        items.append(cur)

    # 展开数组型字段（error_patterns / required_patterns 以 "|" 分隔，兼容 JSON 数组）
    out = []
    for it in items:
        case = dict(it)
        for field in ("error_patterns", "required_patterns"):
            v = case.get(field)
            if isinstance(v, str) and v.startswith("["):
                try:
                    case[field] = json.loads(v)
                except Exception:  # noqa: BLE001
                    case[field] = [p.strip() for p in v.strip("[]").split(",") if p.strip()]
            elif isinstance(v, str) and "|" in v:
                case[field] = [p.strip() for p in v.split("|") if p.strip()]
            elif isinstance(v, str):
                case[field] = [v]
        out.append(case)
    return out


class RegressionRunner:
    def __init__(self, case_dir=CASE_DIR):
        self.cases = load_cases(case_dir)

    # ---------- 执行 ----------
    def run_on_text(self, text, tag=""):
        """对一次技能产出文本跑全部用例。text 为产出内容。"""
        results = []
        for case in self.cases:
            failed_hits = []
            for pat in case.get("error_patterns", []) or []:
                if not pat:
                    continue
                rx = _to_regex(pat)
                hit = (rx.search(text) if rx else (pat in text))
                if hit:
                    failed_hits.append(pat)
            missing_req = []
            for pat in case.get("required_patterns", []) or []:
                if not pat:
                    continue
                rx = _to_regex(pat)
                ok = (rx.search(text) if rx else (pat in text))
                if not ok:
                    missing_req.append(pat)
            passed = (not failed_hits) and (not missing_req)
            results.append({
                "id": case.get("id", "?"), "title": case.get("title", ""),
                "note": case.get("note", ""), "passed": passed,
                "error_hits": failed_hits, "missing_required": missing_req,
            })
        report = self._report(results, tag)
        return {"pass_rate": report["pass_rate"], "passed": report["passed"],
                "total": report["total"], "failed": report["failed"],
                "results": results, "report": report}

    def _report(self, results, tag):
        total = len(results)
        failed = [r for r in results if not r["passed"]]
        passed = total - len(failed)
        pass_rate = (passed / total) if total else 1.0
        report = {
            "ts": time.time(), "tag": tag, "total": total,
            "passed": passed, "failed": len(failed), "pass_rate": pass_rate,
            "fail_items": [{"id": r["id"], "title": r["title"],
                            "error_hits": r["error_hits"],
                            "missing_required": r["missing_required"]} for r in failed],
        }
        fn = os.path.join(REPORT_DIR, "regression_report.jsonl")
        os.makedirs(REPORT_DIR, exist_ok=True)
        with open(fn, "a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")
        return report

    # ---------- 锚点接口（供进化护栏调用） ----------
    @staticmethod
    def record_anchor(anchor_id, text):
        """把已确认修正写为锚点（只增不改，自动去重）。"""
        os.makedirs(_ANCHOR_DIR, exist_ok=True)
        fp = os.path.join(_ANCHOR_DIR, anchor_id.replace("/", "_") + ".anchor.json")
        if os.path.exists(fp):
            return False  # 已存在 -> 不覆盖（锚点不可变）
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"anchor_id": anchor_id, "ts": time.time(),
                       "content": text}, f, ensure_ascii=False)
        return True
