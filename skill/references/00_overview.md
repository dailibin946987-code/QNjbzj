# QNjbzj 全能剧本专家 · 知识资产索引

> 装载本包后按此索引按需加载 references，不必全文常驻上下文。

## 核心入口
| 文件 | 内容 | 何时加载 |
|---|---|---|
| SKILL.md | 包入口：八机制协议 + 路由 + 主流程 | 装载即读 |
| agents/*.md | 六角色职责 | 对应角色出场时 |

## 创作资产（主笔）
| 文件 | 内容 | 何时加载 |
|---|---|---|
| references/01_ly_jbkf_workflow.md | 七步流水线+门控 | 精品剧/电影/长剧创作 |
| references/02_six_gates_aesthetics.md | 六维门控+克制美学+红线 | 每次创作/修改 |
| references/03_dialogue_engine.md | 台词引擎+十要十不要 | 写台词/改台词 |
| references/09_style_modules.md | 短剧/洗稿/分镜速查 | 对应类型任务 |
| references/10_story_structure.md | 结构与节奏知识（叙事框架） | Step2 梗概/Step4 大纲前加载 |
| references/11_visual_language.md | 视听语言知识（视听转换） | Step7 初稿写作按此视听化+格式 |
| references/12_character_dialogue.md | 人物与对白知识（血肉填充） | Step3 人物小传前加载/续写必读 |
| references/13_genre_grammar.md | 剧作知识图谱与类型学（经典理论+番剧爆点语法+台词降噪） | Step2/4 结构定案后参考/类型任务必读 |

## 质检资产（监察者）
| 文件 | 内容 | 何时加载 |
|---|---|---|
| references/04_errorbook_E01-E13.md | 错题本全量+防回退 | 每次交付前扫描 |
| references/08_review_dimensions.md | 七维/六维/导演审核标准 | 审核任务 |

## 运行机制资产（记忆/心跳/进化）
| 文件 | 内容 | 何时加载 |
|---|---|---|
| references/05_memory_protocol.md | 只增记忆+学习信号 | 记忆读写/学习 |
| references/06_heartbeat_protocol.md | 心跳自检 | 阶段间/周期心跳 |
| references/07_evolution_protocol.md | 进化护栏 | 结构性缺陷/改造 |

## 模板（templates/）
| 文件 | 用途 |
|---|---|
| templates/screenplay-format.md | 剧本格式规范 |
| templates/review-report.md | 审核报告 |
| templates/regression-report.md | 自检/回归报告 |

## 工具层（工程级 tools/，宿主有 exec 时挂载；独立于本知识包）
| 文件 | 用途 |
|---|---|
| tools/llm_client.py | OpenAI 兼容 LLM 调用（本地 Ollama 等），local-llm 大脑 |
| tools/memory_store.py | 只增记忆+可选 embedding 检索 |
| tools/errorbook_check.py | 错题本断言执行（内置 E-01~E-13 精简版 + json 用例） |
| tools/heartbeat.py | 心跳自检脚本（保守保洁，只增不删） |

> 注：tools/ 位于工程根目录 D:\D_AIdirector\QNjbzj\tools\，与 skill/ 知识包解耦，可独立复用；宿主无 exec 能力时由对应角色按本包协议人工执行，语义等价。

## 数据目录（data/，宿主无原生记忆时使用）
- data/memory/：四层池记忆（hot/warm/cold/permanent）
- data/anchors/：项目锚点表
- data/errorbook/：错题用例（yaml）
- data/snapshots/：进化快照
- data/logs/：心跳/进化/回归日志

## 创作引用顺序建议
创作任务：01 → 10 → 13(类型学) → 12 → 02 → 03 → 11（穿插）→ 交付前 04/08 监察。
（01 起流程 → 10 立结构 → 13 套类型学爆点语法 → 12 立人物 → 02 过审美 → 03 写台词 → 11 视听化与格式 → 交付前 04/08 监察。）
审核任务：08 → 04（命中时）。
记忆/维护：05/06/07。
