"""心跳执行器：周期发送/超时判定/自动恢复/恢复重放。

心跳循环在独立线程运行，可配置 interval；对超时 Agent 通知 Supervisor 拉起。
"""
import json
import threading
import time

from qn.bus import MessageBus

LOG_PATH = r"D:\D_AIdirector\QNjbzj\data\logs\heartbeat.log"


class HeartbeatExecutor:
    def __init__(self, bus, supervisor, interval=1.0,
                 degraded_threshold=2, down_threshold=3,
                 on_ping=None):
        self.bus = bus
        self.supervisor = supervisor
        self.interval = interval
        self.degraded_threshold = degraded_threshold   # 连续 N 次未应答 -> degraded
        self.down_threshold = down_threshold           # 连续 M 次未应答 -> offline+拉起
        self.on_ping = on_ping or (lambda agent: agent.heartbeat_ping())
        self._missed = {}
        self._stop = threading.Event()
        self._thread = None
        self.last_tick = None
        self.latency = {}

    # ---------- 启停 ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="heartbeat", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            self.tick()
            self._stop.wait(self.interval)

    # ---------- 心跳主逻辑 ----------
    def tick(self):
        agents = list(self.supervisor.agents.values())
        for agent in agents:
            agent_id = agent.agent_id
            alive = False
            t0 = time.time()
            try:
                alive = bool(self.on_ping(agent))
            except Exception:  # noqa: BLE001
                alive = False
            self.latency[agent_id] = time.time() - t0
            if alive:
                self._missed[agent_id] = 0
                self.bus.mark(agent_id, "active")
            else:
                n = self._missed.get(agent_id, 0) + 1
                self._missed[agent_id] = n
                if n >= self.down_threshold:
                    self.bus.mark(agent_id, "offline")
                    self._log("offline", agent=agent_id, missed=n)
                    ok = self._recover(agent_id)
                    self._log("recovered" if ok else "recover_failed",
                              agent=agent_id, ok=ok)
                elif n >= self.degraded_threshold:
                    self.bus.mark(agent_id, "degraded")
                    self._log("degraded", agent=agent_id, missed=n)
                # 未达 degraded 阈值前保持现状（允许瞬时抖动）
        self.last_tick = time.time()

    def _recover(self, agent_id):
        """恢复策略：missed 达阈值即走 Supervisor 重启协议（含恢复重放）。

        用 missed 次数判定而非 last_seen 时间窗，保证心跳判定与拉起动作同源。
        """
        agent = self.supervisor.agents.get(agent_id)
        if agent is None:
            return False
        ok = self.supervisor._restart(agent)
        if ok:
            self._missed[agent_id] = 0
        return ok

    def _log(self, event, **kw):
        entry = {"event": event, "ts": time.time(), **kw}
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
