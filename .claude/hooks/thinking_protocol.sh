#!/bin/bash
printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"每轮对话内化执行按 CLAUDE.md §R 思考协议四步：① 分析 → ② 检索 → ③ 推导 → ④ 执行。\n硬规则：不可以输出标签，以自然对话输出；以 CLAUDE.md §R 为准，禁止用模型默认推理算法替代；上下文中找不到 §R 时立即重读，不擅自启动。"}}\n'
