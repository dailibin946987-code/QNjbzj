"""Supervisor：Agent 运行时进程框架。

职责：注册/启动/停止 Agent；维护心跳看板；超时自动拉起；
     每次输出后强制触发监察回调链（执行与监察分离的运行时强制层）。
"""
import threading
import time

from qn.runtime.agent import AgentStatus

DOWN_AFTER = 3.0      # 秒：超过该时间未应答 -> offline（供心跳判定）
TASK_ISOLATION = True  # run_task 异常隔离：单 Agent 崩溃不拖垮 Supervisor


class Supervisor:
    def __init__(self, bus, down_after=DOWN_AFTER, inspectors=None):
        self.bus = bus
        self.down_after = down_after
        self.agents = {}
        self.inspectors = inspectors or []  # [(agent_id, callable(result)->list[issue])]
        self._lock = threading.RLock()
        self._task_results = []

    # ---------- 注册 / 启停 ----------
    def register(self, agent, auto_start=True):
        with self._lock:
            self.agents[agent.agent_id] = agent
            self.bus.subscribe("*", agent.on_message)
            if auto_start:
                agent.start()
                self.bus.mark(agent.agent_id, "active")
        return agent

    def unregister(self, agent_id):
        with self._lock:
            self.agents.pop(agent_id, None)
            self.bus.mark(agent_id, "offline")

    def stop_all(self):
        for a in list(self.agents.values()):
            a.stop()
        self.bus.mark("*", "offline")  # 清空看板由 bus.mark 语义兼容

    # ---------- 心跳驱动：由 HeartbeatExecutor 周期调用 ----------
    def heartbeat_tick(self):
        """返回 (offline_ids, restarted_ids)。"""
        offline = []
        restarted = []
        now = time.time()
        with self._lock:
            for agent in list(self.agents.values()):
                if agent.status == AgentStatus.STOPPED:
                    continue
                last = agent.last_seen or now
                if now - last > self.down_after:
                    offline.append(agent.agent_id)
                    self.bus.mark(agent.agent_id, "offline")
                    ok = self._restart(agent)
                    if ok:
                        restarted.append(agent.agent_id)
        return offline, restarted

    def _restart(self, agent):
        try:
            agent.stop()
            agent.start()
            agent.restarts += 1
            # 恢复重放：把缓冲期未确认消息重发给该 Agent
            pending = list(agent.handoff_buffer)
            agent.handoff_buffer = []
            for msg in pending:
                try:
                    agent.on_message(msg)
                except Exception:  # noqa: BLE001
                    pass
            self.bus.mark(agent.agent_id, "active")
            return True
        except Exception as exc:  # noqa: BLE001
            self._log("restart_failed", agent_id=agent.agent_id, error=str(exc))
            return False

    # ---------- 任务执行 + 强制监察 ----------
    def run_task(self, agent_id, task):
        """执行任务并强制过监察链。返回 dict(result, inspection)。"""
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"ok": False, "error": "unknown agent: %s" % agent_id}
        try:
            if TASK_ISOLATION:
                outcome = agent.run_task(task)
            else:
                outcome = agent.run_task(task)
            agent.touch()
        except Exception as exc:  # noqa: BLE001
            agent.fail_count += 1
            outcome = {"ok": False, "error": str(exc)}
        issues = self._inspect(agent_id, outcome)
        rec = {"agent_id": agent_id, "result": outcome, "issues": issues,
               "passed": (bool(outcome.get("ok")) and not issues)}
        with self._lock:
            self._task_results.append(rec)
        return rec

    def _inspect(self, agent_id, outcome):
        """强制监察：所有输出必须过监察回调，发现回退立即上报。"""
        issues = []
        for insp_id, cb in self.inspectors:
            try:
                found = cb(outcome) or []
                issues += [{"inspector": insp_id, "issue": i} for i in found]
            except Exception as exc:  # noqa: BLE001
                issues.append({"inspector": insp_id, "issue": "inspector error: %s" % exc})
        return issues

    def _log(self, event, **kw):
        entry = {"event": event, "ts": time.time(), **kw}
        try:
            with open(r"D:\D_AIdirector\QNjbzj\data\logs\supervisor.log", "a", encoding="utf-8") as f:
                import json
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
