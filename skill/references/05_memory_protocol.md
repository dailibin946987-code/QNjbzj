# 永久记忆协议（只增四层池）

> 来源：core/团队记忆 + LY_剧本大脑 蒸馏机制浓缩。铁律：记忆只增不迭代，历史永不删除。

## 一、四层池
| 层 | 容量 | 内容 |
|---|---|---|
| L1 热记忆 | ≤100 条 | 当前会话：active_task / recent_decisions / skill_states |
| L2 温记忆 | ≤500 条 | 近 30 天：successful_patterns / failure_patterns / cross_skill_insights |
| L3 冷记忆 | 归档 | 90 天归档：archived_patterns / historical_stats |
| L4 永久记忆 | 稳定 | core_principles（不可变核心原则）/ anchor_points（不可回退锚点）/ skill_genome（能力基因图谱） |

## 二、蒸馏记忆库（经验卡片四层）
热 ≤10 经验卡片 / 温 ≤50 张（7 天内高频，confidence≥0.8，同类<3 未聚合）/ 冷 ≤200（已聚合原始卡片与废弃法则）/ 永久：active_rules（生效通用法则，按 priority）+ refinement_snapshots（精炼前版本快照）+ evolution_logs + skill_genome_v2。

## 三、记忆条目结构
每条含：id / type / content / source（来源：用户纠正/审核发现/成功实践）/ confidence / reuse_count / created_at / status（tentative/emerging/pending/confirmed/archived）。

## 四、只增协议（硬约束）
1. 新条目一律追加，禁止改写/删除历史条目。
2. 规则变更以"新条目 + 状态标记"表达（旧条目标 ❌ 已失效保留溯源）。
3. 精确保留已确认规则与显式修正；压缩/合并仅限重复冗余条目（心跳协议执行）。
4. 记忆分区物理隔离：全局/项目/会话互不污染。

## 五、学习信号（记忆官执行）
| 信号 | 动作 |
|---|---|
| "No, do X instead" | 高信度，立即记录修正 |
| "I told you before..." | 标记重复并提升优先级 |
| "Always/Never do X" | 提升为偏好 |
| 用户直接编辑你的输出 | 记为试探模式 |
| 同一修正出现 3 次 | 询问是否设为永久 |
| "For this project..." | 写入项目命名空间 |

不触发：沉默（非确认）、单次事件、假设性讨论、第三方偏好、推断偏好（绝不推断）。

修正分类按作用域：Format→global；Technical→domain；Communication→global；Project-specific→项目空间；Person-specific→comms。

## 六、模式演进
Tentative(1次) → Emerging(2次) → Pending(3次待确认) → Confirmed(永久，除非反转) → Archived(90+ 天未用，保留停用)。
反转流程：归档旧模式保留历史 → 记录反转时间戳 → 新偏好记为 tentative。

## 七、宿主落盘适配
- 有原生记忆：按分区命名写入宿主记忆。
- 无记忆能力：写入工作区 `data/memory/{hot,warm,cold,permanent}/`，追加式 markdown/jsonl；同一工作区跨会话复用即永久记忆。
- 有 embedding：向量化检索（nomic-embed-text 等），相似度 >0.85 合并（reuse_count+1、confidence+0.03），否则新增。
