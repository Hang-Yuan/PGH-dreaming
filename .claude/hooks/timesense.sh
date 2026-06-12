# \!/bin/bash
_W=("" "周一" "周二" "周三" "周四" "周五" "周六" "周日")
NOW="$(date '+%Y-%m-%d %H:%M') ${_W[$(date +%u)]}"
printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"当前时间：%s。只在最终面向用户的回复时，第一行按此格式输出（反引号包裹的 inline code，单行，不加任何前后缀）：`%s`。工具调用过程中的中间回复不输出时间戳。"}}\n' "$NOW" "$NOW"
