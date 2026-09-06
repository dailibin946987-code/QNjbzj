---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 06157e2e96c14cf6f2eaaa77c679d68b_6cbb575eaa1111f190de525400461939
    ReservedCode1: bc7fSynuDaxgW3p8tK4e0f3HptKQVz6x6zF+bSaVkygGDZrSK2Ha4A4ZoGMlQt/+8F3q4MR6FjzV4y/FloxbxDfldyzJwaSXWcwVeTvYwjqXLlqj8g9X3Y68ac+FdZTMPxhwqAUDR4jpS1cJqYKBcqd3d7rD1hqdpBcyw/jhRzyY4TktR5iSxFOELZs=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 06157e2e96c14cf6f2eaaa77c679d68b_6cbb575eaa1111f190de525400461939
    ReservedCode2: bc7fSynuDaxgW3p8tK4e0f3HptKQVz6x6zF+bSaVkygGDZrSK2Ha4A4ZoGMlQt/+8F3q4MR6FjzV4y/FloxbxDfldyzJwaSXWcwVeTvYwjqXLlqj8g9X3Y68ac+FdZTMPxhwqAUDR4jpS1cJqYKBcqd3d7rD1hqdpBcyw/jhRzyY4TktR5iSxFOELZs=
---

# QNjbzj · 全能剧本专家技能（运行时工程）

> 定位：把「剧本知识学习报告」指出的四大缺口——Agent 运行时进程框架、心跳执行器、自动化回归验证、全自动进化安全护栏——从"文档规范层"落地为"可运行工程层"。

## 目录结构

```
QNjbzj/
├── qn/                      核心运行时包
│   ├── bus.py              消息总线（沿用 skill-evo-team 的 JSON 消息 schema 与 heartbeat 路由）
│   ├── runtime/
│   │   ├── agent.py        Agent 抽象：注册/启动/停止/崩溃上报
│   │   └── supervisor.py   Agent 运行时进程框架（调度、看板、拉起、graceful shutdown）
│   ├── heartbeat/
│   │   └── executor.py     心跳执行器（周期发送/超时判定/自动恢复/恢复重放）
│   ├── regression/
│   │   └── runner.py       回归验证执行器（错题本用例 -> 可执行断言 -> 报告）
│   ├── evolution/
│   │   └── guardrails.py   全自动进化护栏（快照/沙箱验证/灰度上线/回滚/审计）
│   └── memory/
│       └── store.py        只增记忆存储接口（errors/validated/reference 分区）
├── tests/
│   ├── cases/              回归用例（YAML：从错题本 E-01~E-13 提炼的可执行断言）
│   └── fixtures/           测试夹具（输出样例）
├── data/                   运行时数据（errors/anchors/snapshots/logs，按只增原则写入）
├── examples/demo.py        端到端演示
└── docs/缺口解决方案.md     方案文档（必读）
```

## 快速运行

```powershell
python examples/demo.py
```

demo 会演示：
1. 注册 3 个 Agent 并走总线心跳；
2. 模拟某 Agent 崩溃 -> 心跳超时 -> Supervisor 自动拉起；
3. 跑回归用例（错题本重现检测）；
4. 模拟一次"有害进化"，护栏在回归失败时阻断并回滚。
*（内容由AI生成，仅供参考）*
