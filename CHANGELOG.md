# CHANGELOG

Predictive Generative Harness for Claude Code · **dreaming** 线的模板版本迭代记录。

## 版本号规则

- 本仓库是 PGH **dreaming 线**的独立起点，版本从 `v6.0.0` 起。
- dreaming 与旧 PGH 5.x 模板线分流：两条线互不追溯、互不升级。旧线用户若要迁到 dreaming，按 `§-1` 重新部署。
- 每次发布只记录公开模板结构、入口协议、初始化流程、hook / skill / assistant 骨架变化。

## v6.0.0 · PGH dreaming 新起点

dreaming 把记忆代谢从"每条消息实时判断写入"翻转为**白天零写入、夜间集中代谢**。这是相对旧 5.x 模板线的一次范式重构，不是补丁，因此另起新线、新仓库、新版本号。

### 范式变化

- **实时写入层整层退役**：删除旧版逐消息的 `memory_signal` hook 与 `episodic_inbox.md` 收件箱。白天对话不再实时判断记忆信号，校准信号以原文留在会话转写里。
- **L0 重定义为会话转写**：记忆代谢的唯一输入源改为 Claude Code 运行时自动落盘的 jsonl 转写——完美保真、零维护，取代旧版需要 hook 实时手抄的 inbox。
- **新增 `dream` skill**：夜间无人值守代谢执行者。daily-review 道别时排定一次性定时任务，会话空闲后自动唤醒，回放当日转写完成全部提取、升星、升格、衰减，末步可自动关机。
- **昼夜节律**：白天 close-node 把工作结论固化进工作库；夜间 dream 做全部 schema 代谢；周日 dream 额外承担候选裁决、横向统合、衰减、毕业候选与周归档。

### 记忆池变化

- `episodic_memory.md`（L1）引入**四态**：活动 / 复审 / 候补 / 休眠。单事件信号入候补态等复现；停工项目的模式降入休眠态，免衰减、不占容量、重启即唤醒。
- **项目语境快轨**：高强度工作期同项目多个有效工作日复现的模式可带项目标注快速升 semantic，停工后自动降回 episodic 休眠。
- 记忆池内操作（升降格 / 衰减 / 统合）为 N 级自治，全部写 MEMORY_LOG 留账，用户可事后推翻；只有身份层写入与结构变更需要用户 C 级 verdict。

### hooks / skills

- hooks（5）：`timesense` / `thinking_protocol` / `session_context_check` / `io_batch_check`（新增，提示批量 IO 派 storage-agent）/ `session_end`。删除 `memory_signal`。
- skills（9）：新增 `dream`；`daily-review` / `weekly-review` 薄化为"在场段"——只做需要用户在场的事 + 排梦，不再做记忆池代谢；`close-node` 保留日间 ≥2 独立事件直升 episodic。
- `.claude/agents/storage-agent.md` 承担两 log 读写、长文件落盘、dream 转写分段回放；记忆规则单一权威源在 `assistant/MEMORY/00.memory_agent.md`。

### 文档

- `docs/Predictive Generative Harness System v6.0.md`：PGH 设计主文档（脱敏版），含 dreaming 昼夜节律、网络→线性编译理论、失败驱动演化方法论。
- `docs/核心分流.md`：PGH Core 与 Claude Adapter 分流说明，更新到 dreaming。

### 部署

发 `release v6.0.0` 链接给 Claude Code，由 AI 按 `§-1` 自己完成下载、占位符替换、旧系统检测与迁移、验证、自删。无一键脚本。
