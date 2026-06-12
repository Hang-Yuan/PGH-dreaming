---
name: dream
description: 夜间记忆代谢作业（梦境巩固）。由 daily-review / weekly-review 道别时排定的一次性 durable cron 触发，或 week-sync 昨梦核对派补扫。无人值守执行：回放当日会话转写 → 日级代谢 →（周日）周级载荷 → 巡检 → 落账 →（默认）关机。全部判准 / 阈值 / 授权权威源 = MEMORY/00.memory_agent.md。
updated: 2026-06-12
---

# dream · 夜间记忆代谢

## 加载链

**上游触发**：daily-review §排梦（每日道别后 一次性 durable cron）/ weekly-review 周日载荷标记 / week-sync §昨梦核对（缺梦补扫派单）。

**规则内核**：`<ASSISTANT_ROOT>\MEMORY\00.memory_agent.md` — 全部判准 / 阈值 / 状态机 / 授权的单一权威源，各步开工前按"本步标准"读对应节。

**下游**：`episodic_memory.md` / `semantic_memory.md` + `_archive/semantic_archive.md` / `MEMORY_LOG.md`（派storage-agent）/ `MEMORY/last_dream.md`（一行日期探针，week-sync 昨梦核对）。

**同级联动**：`daily-review`（排梦方 + 在场段分工）/ `weekly-review`（周日载荷定义）/ `close-node`（节点级直升的白天对应物）/ `storage-agent.md`（分段回放读取 + log 落盘）。

---

## 定位

dream 是记忆系统的**唯一夜间代谢执行者**：白天零记忆写入，全部 schema 走向的提取与代谢在此完成。无人值守是常态而非例外。

**无人值守纪律**：
- 任何步骤不阻塞等待回复；需 C verdict 的动作（毕业写入身份层 / 季度归档）只生成候选——记入 MEMORY_LOG dream 条目 + 挂 长期记忆.md §当前处境 上次未决，不执行。
- 只走免审批操作（Bash 追加 / 既有文件 Edit / 派storage-agent）；会弹权限的操作不进夜班。
- 记忆池内全部操作 N 级（→ `00.memory_agent.md §写入授权`），MEMORY_LOG dream 条目全量留账，[用户称呼]可随时推翻。

---

## 作业流程（七步）

### 步骤 1 · 定位当日转写

**本步标准（执行前先读）**：`00.memory_agent.md §L0 回放提取规则`。

按逻辑日期 glob `<CLAUDE_HOME>\projects\` 下当日修改的 jsonl（覆盖当日全部会话）。补扫模式按派单指定日期段，上限 3 个有效工作日。回放深度自判：重日全量、轻日尾段（以当日 `_本周` 流水段数为准）。

### 步骤 2 · 分段回放提取

派storage-agent按块读取转写 → 返回候选信号清单（两轴预标 + 原文锚点 + 涉及项目）；重 IO 子任务可指定低成本模型。主循环逐条按 `00.memory_agent.md §两轴判定` 裁决（提取过滤下限 + 身份层前置过滤）。同时校验事件走向是否已被阶段 A 固化——漏账不补写，记入 MEMORY_LOG dream 条目。

### 步骤 3 · 日级代谢

**本步标准（执行前先读）**：`00.memory_agent.md §episodic_memory 规则 / §升星 / §L0→L1 升格抽象红线 / §项目语境快轨`。

对裁决通过的信号逐条执行：

1. **命中已有条目** → 升星 +1（1 次/日上限）+ 回写最后激活；命中休眠条目 → 唤醒回活动态。
2. **≥2 独立事件** → 升 episodic 活动态（1-3 星）。
3. **单事件值得追踪** → 候补态 ★（7 有效工作日无第二证据自删）。
4. **快轨判定**：同项目 ≥3 有效工作日复现 + 过判准 → 升 semantic 带「语境：项目名」标注（注入组项目语境限额 3）。
5. **跨情景候选提名**：达 ★★★ 且过 `00.memory_agent.md §升格判准` → 直接升格（N 级）或存疑的入候选池留周日梦。
6. 轻量查重：疑似同构标 `待统合簇`；候补到期、容量红区顺手清理。

### 步骤 4 · 周日载荷（条件触发）

排梦任务包带 weekly 载荷标记时执行（定义权威源 = `weekly-review/SKILL.md §周日梦载荷`）：账实核对、候选池重扫、横向统合、episodic 衰减执行、semantic 审查、毕业候选生成（按 `00.memory_agent.md §毕业` 完整流程执行：判型分流 → 三路独立蒸馏 → 收敛判定 → hook 实测验证 → 毕业提案格式输出）、周归档、MEMORY_LOG 周复盘条目。

### 步骤 5 · 巡检面

1. 两池容量扫描报数（→ `00.memory_agent.md §两池容量阈值`）。
2. 跨文件锚点抽查：随机抽 5-8 个 § 指针 grep 验证，死链记入 MEMORY_LOG dream 条目。
3. frontmatter `updated` 与当日实际改动一致性抽查。
4. 活跃项目 progress 转换标记完整性扫描（L2 `新问题` 悬空 / L3 缺承接开出 / 未消费的 `→ 可提取转向模式`）。
5. 休眠 / 候补过期清理（季度审查月份额外做休眠整批出清）。

### 步骤 6 · 落账 + 标记

1. MEMORY_LOG 一条汇总流水定稿 → 派storage-agent追加 `## 操作日志`（格式护栏 → `storage-agent.md §log 写入格式护栏`）。内容含：回放范围 / 升格·升星·唤醒·删除清单 / 漏账提示 / 巡检异常与容量警告 / **待 C 裁决项**。MEMORY_LOG 即账本，不另写汇报文件。
2. **待 C 裁决项**（毕业候选 / 双权威源冲突等）另挂 `长期记忆.md §当前处境` 的「上次未决」一行（启动必读，自然每会话可见直到处理）。
3. **覆盖 `MEMORY/last_dream.md`**：一行逻辑日期（机器探针，仅此一行）。

### 步骤 7 · 关机（条件执行）

排梦任务包带关机指令（默认带；道别时[用户称呼]说留机则不带）→ `shutdown /s /t 60`。本步永远是最后一步；中途任何步骤失败 = 不执行关机（机器还开着 + MEMORY_LOG 缺当晚 dream 条目 = 故障信号）。

---

## 不做

- 不写身份层（USER / SOUL / skill）——毕业候选只记 MEMORY_LOG dream 条目 + 挂 长期记忆.md §上次未决等 C verdict。
- 不动 hook / settings / 协议层文件；不补写工作库（漏账只报不补）。
- 不直接 Read/Edit 两 log（一律派storage-agent）。
- 不在白天被调用（白天的记忆动作只有 close-node 节点级直升一种）。
