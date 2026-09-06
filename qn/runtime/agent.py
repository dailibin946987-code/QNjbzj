"""Agent 抽象：一个技能/角色 = 一个 Agent 实例。"""
import abc
import time


class AgentStatus:
    REGISTERED = "REGISTERED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class Agent(abc.ABC):
    """基类。子类需实现 run_task；可按需覆写 on_message / check。

    - on_message(msg)：处理总线消息（订阅回调，Supervisor 统一注入）。
    - check()：心跳探活回调。抛异常或返回 False 视为本轮失活。
    - run_task(task)：执行一次主任务。默认空实现，由具体技能 Agent 覆写。
    """

    def __init__(self, agent_id, name="", role=""):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.role = role
        self.status = AgentStatus.REGISTERED
        self.last_seen = None
        self.fail_count = 0
        self.restarts = 0
        self.handoff_buffer = []  # 恢复重放用：未确认消息缓存

    # ---- 生命周期 ----
    def start(self):
        self.status = AgentStatus.STARTED
        self.touch()

    def touch(self):
        self.last_seen = time.time()

    def stop(self):
        self.status = AgentStatus.STOPPED

    # ---- 可覆写钩子 ----
    def on_message(self, msg):  # 默认：非心跳消息进缓冲，等待 Supervisor 确认
        h = msg["header"]
        if h.get("type") != "heartbeat":
            self.handoff_buffer.append(msg)

    def check(self):  # 默认探活：只要进程线程活着即算在线
        return True

    @abc.abstractmethod
    def run_task(self, task):
        """执行一次任务。成功返回 (ok=True, result=...)，失败抛异常或返回 (ok=False, error=...)。"""
        raise NotImplementedError

    # ---- 心跳侧 ----
    def heartbeat_ping(self):
        self.touch()
        return self.check()
