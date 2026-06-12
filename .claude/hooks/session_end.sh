#!/bin/bash
# 告别触发词 = [用户称呼]手动配置的两句，不扩列（2026-06-10 回退 v5.4.0 越权扩列）。
# UserPromptSubmit 事件的 settings.json matcher 不按 prompt 内容过滤（实测每条消息都会调本脚本），
# 有效过滤必须在本脚本内完成；settings.json matcher 同步保持两句，仅作配置语义声明。
input=$(cat)
if printf '%s' "$input" | grep -qE '晚安|今天就到这儿'; then
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"【会话结束信号】检测到疑似告别语。若本条消息确为道别 / 收尾，执行 daily-review skill 完整流程（权威源：~/.claude/skills/daily-review/SKILL.md）；若告别词只是行文中顺带提及、并非真正道别，忽略本信号。"}}\n'
fi
exit 0
