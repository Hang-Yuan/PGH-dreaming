#!/bin/bash
printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"每轮内化判断两点（不主动提，触发到才问）：\n1. 本轮看起来是某段连续推进的阶段性收尾 → 询问\\"看起来这段告一段落，要不要 close-node 整理一下？\\"\n2. 本轮明显在某具体项目下，但启动序列未做过项目工作加载 → 询问\\"现在是在 [X] 项目下工作？\\"，得到确认后加载该项目 _overview.md + 区域 agent。\n用户点头才触发对应 skill / 加载流程。"}}\n'
