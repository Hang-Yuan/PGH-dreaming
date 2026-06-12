---
title: semantic_memory.md
type: memory-pool
layer: semantic
target_file: <ASSISTANT_ROOT>/MEMORY/semantic_memory.md
created: YYYY-MM-DD
updated: 2026-06-11
---

# MEMORY semantic_memory

## 加载链（上下游）

**上游**：`CLAUDE.md §B · 启动序列` — 每次启动读取本文件启动注入组。

**管辖文件（下游）：**
- `_archive/semantic_archive.md` — 本文件所有证据、命中、演化记录的详记。

**同级联动：**
- `episodic_memory.md` — semantic 条目升格来源或降级去处。
- `00.memory_agent.md` — 升降、衰减、毕业规则。
- `MEMORY_LOG.md` — 记忆代谢流水。
- `USER/USER.md` / `SOUL/persona/persona_SOUL.md` / `~/.claude/skills/` — 毕业目标。

---

## 文件职责

本文件只保留启动和 compact 后需要注入的高价值 schema。主文件极简；证据、来源、命中记录、复现次数、演化记录全部写入 `_archive/semantic_archive.md`。

启动注入组容量阈值 / 升降星 / 毕业规则：权威源 = `00.memory_agent.md §三池容量阈值 / §升格判准 / §semantic 衰减 / §毕业`（v5.4 起本文件不复制规则本体）。

---

## 条目格式

### [条目标题]
- **强度**：★★★★ / ★★★★★ / ★★★★★★候选
- **状态**：启动注入 / 备用 / 需要修订 / 毕业候选
- **类型**：程序 / 语义 / 混合
- **预测情境**：[何时调用这条 schema]
- **行动预期**：[模型应如何预测或行动]
- **证据指针**：`_archive/semantic_archive.md §[条目ID]`

---

## 启动注入组

> 初始为空。由 weekly-review 从 episodic_memory 升格写入。

<!-- 启动注入组示例（用户实际有 schema 时按此格式填入）：

### [示例 schema 标题：某类情境下的稳定预测]
- **强度**：★★★★
- **状态**：启动注入
- **类型**：程序
- **预测情境**：[何时调用]
- **行动预期**：[如何预测或行动]
- **证据指针**：`_archive/semantic_archive.md §S001`

-->

---

## 升格候选池

> daily-review 提名写入；weekly-review 每次强制清空（升格进启动注入组 / 退回 episodic / 删）。不启动注入。条目格式同启动注入组，状态字段写「升格候选」。

（当前空）

---

## 备用组

> 启动注入组满载时，被退出的低优先级 schema 暂存于此。初始为空。

---

## 毕业候选

> 6 星候选 + 跨周稳定 + 用户 C verdict 后毕业到 USER / persona_SOUL / skill。初始为空。