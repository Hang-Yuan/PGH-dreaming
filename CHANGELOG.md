# CHANGELOG

Predictive Generative Harness for Claude Code · **dreaming** 线的模板版本迭代记录。

## 版本号规则

- 本仓库是 PGH **dreaming 线**的独立起点，版本从 `v6.0.0` 起。
- dreaming 与旧 PGH 5.x 模板线分流：两条线互不追溯、互不升级。旧线用户若要迁到 dreaming，按 `§-1` 重新部署。
- 每次发布只记录公开模板结构、入口协议、初始化流程、hook / skill / assistant 骨架变化。

## v6.1.0 · semantic 退注入 + meta-skill 蒸馏器 + 记忆系统结构

dreaming 起点之后第一次 feature 级更新：三块——记忆架构（semantic 退出启动注入）、新增 meta-skill（把判断工作流蒸馏成 SKILL.md 的元 skill）、memory_agent 补全结构性全景节。

### 记忆架构变化

- **semantic 退出启动注入**：`semantic_memory.md` 从"启动注入层"降级为 **dream 中间工作区**——白天不进运行时上下文，仅夜间被 dream 作为代谢对照基线读取。白天运行时的共同世界模型底座收缩为 **USER + SOUL + CLAUDE.md §R 三件套身份层**。启动序列由 7 步精简为 5 步（删 semantic 读取 + storage-agent 日志读取两步）。
- **升格门重构**：跨情景 episodic → semantic 的唯一升格门改为**周日横向统合**；`★★★ 再命中` 从升格触发器重定义为**怀疑触发器**（标 `待统合簇` 留周日判去向），避免母结构的多个表面各自单条升格、碎片化 semantic。
- **代谢对照基线显式化**：明确两轴判定本质是差分运算，对照基线 = 现有 schema 全集三层（episodic / semantic / 身份层），各自比对对象与角色成文。

### skills

- **新增 `meta-skill`**：把一条「长链复杂判断工作流」蒸馏成可自动执行的 SKILL.md 的元 skill。9 步流程（锁定目标函数 → 切执行段/判断节点 → 四相位挖三件套 → 判据分流 → 缺料推理 → 编码 → 触发 eval → 检验回流 → Improve 迭代），含 `scripts/`（机械闸 validate / 指针审 anchor_check / eval 编排）+ `references/`（schemas / verification）+ `agents/`（grader / comparator / analyzer）+ eval-viewer。吸收 Anthropic skill-creator 2.0 工程检验层。
- **移除 `manage-research-reference`**：文献容器 `_reference/` 的创建内联进 `create-project`（科研类项目首次需要文献时直接建 + `文献记录.md`），不再单设专用 skill。skills 数 9 不变（9 原有 − 1 + meta-skill）。
- `dream` / `weekly-review` / `week-sync`：同步 semantic 退注入口径（"启动注入组"→"活跃组"）；`dream` 流程补容量扫描独立步 + 代谢对照基线在场约束。

### 文档

- `assistant/MEMORY/00.memory_agent.md`（→ v5.8.0）：新增 `## 记忆系统结构` 全景节（schema 定义 / 信息流与分流图 / 代谢对照基线 / 生命周期）；零上下文 agent 仅凭本节即可推导代谢该和什么比对。
- `.claude/CLAUDE.md §R` 思考协议加深：协议是"遇到问题就启动的处理机"（不止每轮开头）；执行中遇新问题返回 ② 重检索（非返回 ③）。

## v6.0.2 · daily-review 排后核验降级容错

`daily-review` skill 排梦步骤的「排后核验」增加降级路径：CronList 工具调用解析失败时不阻断流程，改以 CronCreate 成功回执作替代证据，步骤 7 道别时明示核验降级，留 `last_dream` / MEMORY_LOG 事后地面确认，明早 week-sync 接住。

### skills

- `daily-review` 步骤 6 排后核验：CronList 失败 → 降级核验而非阻断道别流程。



移除 v6.0.0 引入的 `io_batch_check` hook。该 hook 在 IO 工具调用时注入"批量 IO 打包派 storage-agent"提醒，实践中判定为伪护栏：

- **不基于真实成本**：只统计转写最近若干行的 IO 调用次数，与实际 token / 开销无关，触发与否不对应成本。
- **不改变权限**：只注入 additionalContext 文本，不做 permissionDecision，对真正要防的 sub-agent 扇出失控没有硬约束力。
- **重复注入吃上下文**：达阈值后每次 IO 调用重复注入同一句，反而消耗主会话上下文。

IO 经济真正靠 sub-agent 工具白名单（storage-agent 承接批量 IO）与主会话派单纪律，不靠这条软提醒。

### hooks

- hooks 由 5 个减为 4 个：`timesense` / `thinking_protocol` / `session_context_check` / `session_end`。移除 `io_batch_check`。

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
