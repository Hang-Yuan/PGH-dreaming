#!/bin/bash
# io_batch_check.sh — PreToolUse hook：主会话连续 IO 检测，超阈值提醒打包派storage-agent
# v5.5.2 新建。只注入提醒，不输出 permissionDecision（不改变权限行为）。
input=$(cat)
transcript=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | head -1 | sed 's/"transcript_path":"//;s/"$//')
if [ -z "$transcript" ] || [ ! -f "$transcript" ]; then
  exit 0
fi
# 最近 60 行 jsonl ≈ 最近 20-30 轮；统计主会话 IO 工具调用密度（兼容原生名与 mcp 全名）
count=$(tail -n 60 "$transcript" | grep -o '"name":"\(Read\|Edit\|Write\|Grep\|Glob\|mcp__tools__read\|mcp__tools__edit\|mcp__tools__write\|mcp__tools__grep\|mcp__tools__glob\)"' | wc -l)
if [ "$count" -ge 8 ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"⚠ 最近窗口内主会话已 %s 次 IO 工具调用——批量 IO 应打包派storage-agent（storage-agent），主会话只留裁决；继续散跑会按全量上下文重复计费。"}}\n' "$count"
fi
exit 0
