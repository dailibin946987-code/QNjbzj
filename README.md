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

> 定位：把「剧本知识学习报告」指出的四大缺口——Agent 运行时进程框架、心跳执行器、自动化回归验证、全自动进化安全护栏——从"文档规范层"落地为"可运行工程层"；并把 skill-evo-team 剧本成套资产沉淀为**宿主无关的全能剧本专家包**（跨 WorkBuddy / 本 Agent / 其他智能体通用）。

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
├── skill/                   全能剧本专家知识包（宿主无关，纯文本协议）
│   ├── SKILL.md             包入口：八机制协议 + 六角色 + 大脑模式桥接 + 路由
│   ├── agents/              六角色协议（导演/主笔/监察者/记忆官/进化官/心跳官）
│   ├── references/          方法论资产（七步流水线/六维审美/台词引擎/错题本 E-01~E-14/记忆/心跳/进化/审核/风格路由/索引）
│   └── templates/           输出模板（剧本格式/审核报告/回归报告）
├── tools/                   机器校验与增强工具（宿主有 exec 时挂载，标准库免依赖）
│   ├── llm_client.py        OpenAI 兼容 LLM 调用（本地 Ollama 等，local-llm 大脑）
│   ├── memory_store.py      只增记忆 + 可选 embedding 检索
│   ├── errorbook_check.py   错题本断言执行器（内置 E-01~E-14 精简版）
│   └── heartbeat.py         心跳自检脚本（保守保洁，只增不删）
├── tests/
│   ├── cases/              回归用例（YAML：从错题本 E-01~E-14 提炼的可执行断言）
│   └── fixtures/           测试夹具（输出样例）
├── data/                   运行时数据（errors/anchors/snapshots/logs/memory，按只增原则写入）
├── examples/
│   ├── demo.py             端到端演示（运行时/心跳/回归/进化护栏）
│   └── smoke_test.py       冒烟测试（结构完整性 + 工具运行 + 可选 LLM 探测）
└── docs/
    ├── 缺口解决方案.md      方案文档（必读）
    ├── 宿主接入指南.md      通用化装载指南（给任意宿主的一条指令）
    └── 验证报告.md          完整验证报告
```

## 快速运行

```powershell
python examples/demo.py              # 运行时四大机制端到端演示
python examples/smoke_test.py        # 冒烟测试（含结构完整性）
python examples/smoke_test.py --llm-probe   # 追加本地 LLM 探测
```

demo 会演示：
1. 注册 3 个 Agent 并走总线心跳；
2. 模拟某 Agent 崩溃 -> 心跳超时 -> Supervisor 自动拉起；
3. 跑回归用例（错题本重现检测）；
4. 模拟一次"有害进化"，护栏在回归失败时阻断并回滚。

工具脚本（任意宿主可复用）：
```powershell
python tools\errorbook_check.py check "台词文本"   # 错题断言（E-01~E-14）
python tools\heartbeat.py                          # 心跳自检
python tools\memory_store.py add permanent anchors "P001|规则" --note 来源
python tools\llm_client.py --list                  # 探测本地 Ollama
python tools\llm_client.py chat "写一句离别台词"    # 本地 LLM 创作
```

## 大脑模式
| 模式 | 使用方 | 说明 |
|---|---|---|
| host-brain | WorkBuddy 等原生 LLM 宿主 | 宿主模型按 skill/ 协议执行 |
| local-llm | 本机 Ollama（qwen2.5:14b 等） | tools/llm_client.py 桥接，离线可跑 |
| tool-assisted | 本 Agent / 其他 Agent | 自身推理 + 机器校验（断言/记忆/心跳） |

*（内容由AI生成，仅供参考）*
