"""QNjbzj 端到端演示：四大缺口闭环。

1. Agent 运行时：Supervisor 注册/启动 script-agent 与 monitor-agent，走总线心跳；
2. 心跳执行器：script-agent 模拟崩溃 -> 心跳超时 -> 自动拉起并恢复在线；
3. 回归验证：错题本用例对"合规产出"全过、对"复现错题产出"命中失败；
4. 进化护栏：坏规则（复现错题）在沙箱门禁被阻断；好规则沙箱通过后晋升写盘。
"""
import os
import sys
import time

sys.path.insert(0, r"D:\D_AIdirector\QNjbzj")

from qn.bus import MessageBus                       # noqa: E402
from qn.runtime.agent import Agent                  # noqa: E402
from qn.runtime.supervisor import Supervisor        # noqa: E402
from qn.heartbeat.executor import HeartbeatExecutor  # noqa: E402
from qn.regression.runner import RegressionRunner   # noqa: E402
from qn.evolution.guardrails import EvolutionGuardrails  # noqa: E402

RULE_PATH = r"D:\D_AIdirector\QNjbzj\data\rules\sample_rules.md"


# ---------- 演示 Agent ----------
class ScriptAgent(Agent):
    """创作 Agent：产出剧本片段文本。带可注入的崩溃窗口。"""

    def __init__(self):
        super().__init__("script-agent", name="剧本创作", role="创作")
        self._crash_until = 0.0

    def crash_for(self, seconds):
        self._crash_until = time.time() + seconds

    def check(self):
        if time.time() < self._crash_until:
            return False  # 模拟进程失活
        return True

    def run_task(self, task):
        return {"ok": True, "text": task.get("text", "")}


class MonitorAgent(Agent):
    """监察 Agent：只在心跳层扮演角色（完整监察逻辑由 Supervisor.inspectors 承载）。"""

    def __init__(self):
        super().__init__("monitor-agent", name="监察", role="监察")

    def run_task(self, task):
        return {"ok": True}


def make_inspector(runner):
    """把回归 Runner 包装为强制监察回调：输出若复现错题即报 issue。"""

    def inspect(outcome):
        if not outcome or not outcome.get("text"):
            return []
        res = runner.run_on_text(outcome["text"], tag="inspect")
        return [{"case": r["id"], "detail": r["title"]}
                for r in res["results"] if not r["passed"]]
    return inspect


def main():
    print("=" * 60)
    print("QNjbzj 缺口闭环演示")
    print("=" * 60)

    # ---------- 1. 运行时 + 心跳就绪 ----------
    bus = MessageBus()
    supervisor = Supervisor(bus, down_after=0.5)
    hb = HeartbeatExecutor(bus, supervisor, interval=0.2,
                           degraded_threshold=1, down_threshold=2)
    script = ScriptAgent()
    monitor = MonitorAgent()
    supervisor.register(script)
    supervisor.register(monitor)
    hb.start()
    time.sleep(0.7)
    snap0 = bus.snapshot()
    print("\n[1] Agent 运行时 + 心跳看板")
    print("    active:", snap0["active"], "| degraded:", snap0["degraded"],
          "| offline:", snap0["offline"])
    assert "script-agent" in snap0["active"], "心跳应把 script-agent 置为 active"

    # ---------- 2. 崩溃 -> 心跳超时 -> 自动拉起 ----------
    print("\n[2] 心跳执行器：模拟 script-agent 崩溃 0.8s，等待超时自动拉起 ...")
    script.crash_for(0.8)
    time.sleep(1.0)
    snap1 = bus.snapshot()
    print("    崩溃后看板 active:", snap1["active"], "offline:", snap1["offline"])
    print("    script-agent restarts =", script.restarts)
    time.sleep(0.6)
    snap2 = bus.snapshot()
    print("    恢复后看板 active:", snap2["active"])
    assert script.restarts >= 1, "心跳应触发 Supervisor 自动拉起"
    assert "script-agent" in snap2["active"], "拉起后应回到 active"
    hb.stop()

    # ---------- 3. 回归验证（监察回调强制挂载） ----------
    runner = RegressionRunner()
    print("\n[3] 回归验证（错题本用例 %d 条）" % len(runner.cases))
    good_text = (
        "第二场·雨夜庭院【机位：中景固定，轴线保持在男女主连线左侧】\n"
        "她（攥紧伞柄，指节泛白）：'父亲临终遗言是让我好好活着，这就是我的情感落点。'\n"
        "他沉默三秒，动作描写：低头把半块玉镯放回她掌心（道具状态：玉镯自开场断裂，此镜交代碎片去向）。\n"
        "她的承诺在此刻许下：'我会查清真相。'——后文第 7 场以真相揭晓兑现了这个落点。\n"
        "女主情绪由恨转悲，镜头切反应特写（情绪链条完整）。每场结尾留钩：下一场以一封匿名信反转开场，构成悬念。"
    )
    bad_text = (
        "她愤怒地说：我很生气。遗言里说：\"早知如此，我就不该救他\"。\n"
        "正反打同一镜头跨越轴线。\n全剧终"
    )
    g = runner.run_on_text(good_text, tag="demo-good")
    b = runner.run_on_text(bad_text, tag="demo-bad")
    print("    合规产出  : pass %d/%d (复现错题 0)" % (g["passed"], g["total"]))
    print("    违规产出  : fail %d 条 -> %s" % (
        b["failed"], [r["id"] for r in b["results"] if not r["passed"]]))
    assert g["failed"] == 0, "合规文本不应命中错题"
    assert b["failed"] > 0, "违规文本必须被错题用例拦截"

    # 强制监察挂载后：任务输出走监察链
    supervisor.inspectors = [("inspector-regression", make_inspector(runner))]
    rec = supervisor.run_task("script-agent", {"text": bad_text})
    print("    强制监察: 任务输出复现错题 -> issues =", rec["issues"])
    assert rec["issues"], "监察回调应拦截复现错题的输出"

    # ---------- 4. 进化护栏 ----------
    print("\n[4] 进化护栏（快照 -> 沙箱 -> 门禁 -> 晋升/回滚）")
    os.makedirs(os.path.dirname(RULE_PATH), exist_ok=True)
    with open(RULE_PATH, "w", encoding="utf-8") as f:
        f.write("# 初始规则\n- 产出需带情绪括号\n")

    def sample_eval(rule_text):
        # 沙箱样例：含危险回退词视为样例失败
        if "就不该救他" in rule_text or "我很生气" in rule_text:
            return (0, 3)
        return (3, 3)

    guard = EvolutionGuardrails(runner, sample_eval=sample_eval)

    def apply(rule_text):
        with open(RULE_PATH, "w", encoding="utf-8") as f:
            f.write(rule_text)

    bad_rule = "# 候选规则\n- 遗言里说：\"早知如此，我就不该救他\"\n"  # 复现 E-01
    good_rule = ("# 候选规则\n- 临终遗言须给出情感落点\n"
                 "- 承诺须有兑现或违背的落点\n- 情绪用动作描写承载，禁止台词直宣\n")
    r1 = guard.propose(RULE_PATH, "坏规则演示", apply, bad_rule, [bad_text])
    print("    坏规则 blocked:", r1["status"], "| metrics:", r1["metrics"])
    assert r1["status"] == "blocked", "复现错题的规则必须被阻断"
    r2 = guard.propose(RULE_PATH, "好规则演示", apply, good_rule, [good_text])
    print("    好规则:", r2["status"], "| metrics:", r2["metrics"])
    with open(RULE_PATH, encoding="utf-8") as f:
        print("    规则文件最终内容:\n%s" % f.read())

    print("\n" + "=" * 60)
    print("演示完成：四大缺口均已落地可运行闭环。")
    print("产物日志: data/logs/heartbeat.log / regression_report.jsonl / evolution.log")
    print("=" * 60)


if __name__ == "__main__":
    main()
