# 心跳自检协议

> 来源：utils/self-improving/heartbeat-rules.md 通用化。心跳目的：保持记忆系统整洁可信；大多数心跳应无事可做。

## 一、原则
- 心跳是**保守保洁**，不是主动改造。
- 无明确违反规则时不做任何事。
- 优先追加/摘要/索引修复，禁止大改。

## 二、心跳流程（每次）
1. 记录开始：写 last_heartbeat_started_at（ISO8601）。
2. 读取上次复查点 last_reviewed_change_at。
3. 扫描该时间之后的变更文件（记忆/锚点/错题/状态；排除 state 文件自身）。
4. 无变更 → 置 HEARTBEAT_OK，追加 "no material change"，结束。
5. 有变更 → 保守整理：刷新索引 / 合并重复或压缩冗长条目 / 仅在目标明确时移动错放笔记 / 精确保留已确认规则与显式修正。
6. 干净完成才更新 last_reviewed_change_at；记录 last_heartbeat_result 与 last_actions。

## 三、心跳绝不做的（安全红线）
1. 永不删除数据、清空文件或覆盖不确定文本。
2. 不重组记忆目录（data/memory 等）外的文件。
3. 范围不明 → 不动，记录建议后续处理。
4. 不把"看起来可以优化"当成"必须优化"。

## 四、状态字段
state 文件字段：last_heartbeat_started_at / last_reviewed_change_at / last_heartbeat_result / last_actions。

## 五、宿主适配
- 有定时能力：注册周期心跳（如每小时/每天），prompt 建议："执行 QNjbzj 心跳自检：扫描 data/memory 等记忆文件在 last_reviewed_change_at 之后的变更，按心跳协议保守整理（只增、索引刷新、合并冗余），无变更记录 HEARTBEAT_OK，禁止删除或覆盖不确定内容。"
- 无定时能力：作为交付完成后的内部自检步骤执行，不打扰用户。

## 六、心跳与记忆的配合
- 记忆条目膨胀 → 心跳负责索引与合并（不动内容）。
- 锚点表定期瘦身（合并重复、归档失效）→ 心跳执行，历史保留。
