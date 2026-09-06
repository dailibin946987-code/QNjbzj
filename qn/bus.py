"""QNjbzj 消息总线：沿用 skill-evo-team 的 JSON 消息 schema 与 heartbeat 路由。"""
import json
import threading
import time
from collections import defaultdict


class MessageBus:
    """轻量进程内总线。

    消息格式：{"header": {"type": str, "from": str, "to": str|None,
                           "routing_key": str, "ts": float},
               "body": {...}, "trace": {...}}
    路由：subscriber 按 routing_key 前缀订阅，topic 支持 'xxx.*' 通配末段。
    """

    HEARTBEAT_KEY = "team.heartbeat"
    EVOLUTION_KEY = "team.evolution"
    ALERT_KEY = "team.alert"

    def __init__(self):
        self._subs = defaultdict(list)  # routing_key_prefix -> [callback]
        self._lock = threading.RLock()
        self._stats = defaultdict(int)
        self.health = {"active": set(), "degraded": set(), "offline": set()}

    # ---------- 订阅 / 发布 ----------
    def subscribe(self, routing_key_prefix, callback):
        with self._lock:
            self._subs[routing_key_prefix].append(callback)

    def publish(self, msg_type, frm, body=None, to=None, routing_key=None):
        msg = {
            "header": {
                "type": msg_type, "from": frm, "to": to,
                "routing_key": routing_key or msg_type, "ts": time.time(),
            },
            "body": body or {}, "trace": {},
        }
        self._deliver(msg)
        return msg

    def _deliver(self, msg):
        key = msg["header"]["routing_key"]
        with self._lock:
            targets = []
            for prefix, cbs in list(self._subs.items()):
                if key == prefix or key.startswith(prefix + ".") or prefix == "*":
                    targets.extend(cbs)
        delivered = 0
        for cb in targets:
            try:
                cb(msg)
                delivered += 1
            except Exception as exc:  # noqa: BLE001 订阅者异常不得拖垮总线
                self._stats["subscriber_error"] += 1
                self._stats["last_error"] = str(exc)
        self._stats[key] += delivered
        return delivered

    # ---------- 看板 ----------
    def mark(self, agent_id, status):
        """status: active / degraded / offline"""
        with self._lock:
            for s in self.health.values():
                s.discard(agent_id)
            self.health[status].add(agent_id)

    def snapshot(self):
        with self._lock:
            return {
                "active": sorted(self.health["active"]),
                "degraded": sorted(self.health["degraded"]),
                "offline": sorted(self.health["offline"]),
                "stats": dict(self._stats),
            }
