# eval workspace 数据结构（meta-skill 第 8-9 步 references）

被 `SKILL.md §第 8 步` `§第 9 步` 引用。定义 eval workspace 里所有 JSON 文件的**形状**——字段名、嵌套、取值。
本文件只管「数据长什么样」；「怎么评、阈值多少、pass^k 怎么算」是方法，在 `references/verification.md`，不在这里复写。
骨架取自 Anthropic skill-creator 2.0 schemas（来源见 verification.md §来源）；本系统两臂适配项标 `本系统加`。

JSON key 一律英文（机器读 + 与 Anthropic 工具对齐）；本文件说明用中文。

---

## 0 · eval_type — 贯穿所有 schema 的分叉（本系统加）

Anthropic 假设 skill 产出一个 artifact，用 assertion 给 artifact 打分。本系统的 skill 分两类，**每条 eval 必带 `eval_type`**，下游 grading / benchmark / viewer 全按它分流：

| eval_type | 适用 skill | 判什么 | 主指标 |
|---|---|---|---|
| `end_state` | 有真实终态产物（招投标决策、write-progress 类） | artifact 对不对 → assertion pass/fail | `pass_rate` |
| `route_convergence` | 不可逆 / DRY RUN / 无终态（dream、daily-review、week-sync 类） | 3 路盲跑是否走同分支 + 路由对不对 | `convergence_rate` |

- 一个 workspace 内允许混装两类 eval（一份 skill 可能既有终态产物又有路由判断），逐条 eval 看自己的 `eval_type`。
- 凡下面字段标 `[A]` = 仅 end_state；`[B]` = 仅 route_convergence；无标 = 两类通用。

---

## 1 · 目录布局

eval workspace **不进 skill 文件夹**（进了会被 validate.py 判杂物、污染搬上运行时目录的干净件）。默认住当前工作目录下的 `_meta_eval_workspace/`；也可用脚本的 `--root` 指到任意开发区：

```
_meta_eval_workspace\<目标skill名>\
├── evals\
│   └── evals.json                 任务集（带 eval_type）
├── history.json                   版本胜负账（Improve 模式，workspace 根）
├── trigger_eval\
│   ├── trigger_set.json           触发用例（should_trigger 数组，人手填）
│   ├── _split.json                prepare 产出：train/test 切分 + 被测 description
│   ├── _judge_card.md             prepare 产出：给 agent 派判定 sub-agent 的现成卡
│   ├── judging\<version>\run*.json  agent 派的 sub-agent 写回的判定（多数票）
│   └── result.json                score 产出（best_description + 各版本 train/test）
├── iteration-1\
│   ├── eval-0-with_skill-run1\
│   │   ├── outputs\               执行产物（含 metrics.json）
│   │   ├── transcript.md          执行转写
│   │   ├── timing.json
│   │   └── grading.json
│   ├── eval-0-without_skill-run1\ 基线（同结构）
│   ├── ...                        run 目录名 = eval-{id}-{config}-run{N}，N 从 1 起
│   └── benchmark\
│       ├── benchmark.json
│       └── benchmark.md
├── iteration-2\                   Improve 模式重跑落这里
│   └── ...（含 comparison-N.json / analysis.json）
└── review\
    └── review.html                generate_review --static 产物
```

`<run-dir>` = 形如 `iteration-N/eval-K-with_skill/` 的单次执行目录。下面凡说"run 根""outputs"皆相对它。

---

## 2 · evals.json（`evals/evals.json`）

任务集。两类 eval 共表，逐条按 `eval_type` 带不同字段。

```json
{
  "skill_name": "dream",
  "evals": [
    {
      "id": 0,
      "eval_type": "end_state",
      "prompt": "用户任务 prompt（原样喂给执行 sub-agent）",
      "files": [],
      "expected_output": "期望产物的文字描述",
      "expectations": [
        "可客观验证的断言1（描述性命名见 eval_metadata）",
        "断言2"
      ]
    },
    {
      "id": 1,
      "eval_type": "route_convergence",
      "prompt": "触发该 skill 的任务 prompt",
      "files": [],
      "expected_route": "已知正确路由（reference solution：该走哪个分支 / 哪几步）",
      "reference_solution": "为什么这条路由对——判断依据，供 grader code-grade 路由结论",
      "dry_run": true
    }
  ]
}
```

- `files`：可选，任务附带的输入文件路径（招标文件、案例集等）。空数组 = 纯 prompt。
- `[A] expected_output` / `expectations[]`：assertion 在 eval_metadata.json 里展开成带名条目。
- `[B] expected_route` / `reference_solution`：路由层 reference，**不评说辞、不评 tool-call 序列**（见 verification.md §DRY-RUN 特化）。
- `[B] dry_run`：true = 令执行 sub-agent 声明动作不真做（skill 含改文件 / 建 cron / 删数据时必 true）。

## 3 · eval_metadata.json（`<run-dir>` 同级，每条 eval 一份）`[A]`

仅 end_state 用。把 evals.json 的 `expectations` 字符串展开成带名断言，供 grader 引用。

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "用户任务 prompt",
  "assertions": [
    { "name": "has-axis-labels", "text": "图表含坐标轴标签" }
  ]
}
```

route_convergence 不产此文件（它的 reference 在 evals.json 的 expected_route）。

---

## 4 · grading.json（`<run-dir>/grading.json`）

grader agent 产出（见 `agents/grader.md`）。**按 eval_type 分叉**。

### 4A · end_state 形态

```json
{
  "eval_type": "end_state",
  "expectations": [
    { "text": "断言原文", "passed": true, "evidence": "引用转写/产物里的证据" }
  ],
  "summary": { "passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67 },
  "execution_metrics": {
    "tool_calls": { "Read": 5, "Write": 2, "Bash": 8 },
    "total_tool_calls": 15, "total_steps": 6, "errors_encountered": 0,
    "output_chars": 12450, "transcript_chars": 3200
  },
  "timing": { "executor_duration_seconds": 165.0, "grader_duration_seconds": 26.0, "total_duration_seconds": 191.0 },
  "claims": [ { "claim": "...", "type": "factual", "verified": true, "evidence": "..." } ],
  "user_notes_summary": { "uncertainties": [], "needs_review": [], "workarounds": [] },
  "eval_feedback": { "suggestions": [ { "assertion": "...", "reason": "..." } ], "overall": "..." }
}
```

- `expectations[]` 三字段 `text` / `passed` / `evidence` 名字固定不可改（viewer 依赖）。
- `claims[].type` ∈ `factual` / `process` / `quality`。
- `pass_rate` 取值 0.0–1.0。
- `eval_feedback`：grader 对断言本身的批评（断言太弱会通过劣质产物 → 假信心）。

### 4B · route_convergence 形态（本系统加）

```json
{
  "eval_type": "route_convergence",
  "route_result": {
    "expected_route": "evals.json 里的 reference",
    "actual_route": "本次 sub-agent 实走的分支",
    "route_match": true,
    "evidence": "转写里走该分支的证据原文",
    "stuck": []
  },
  "execution_metrics": { "...": "同 4A" },
  "timing": { "...": "同 4A" },
  "eval_feedback": { "suggestions": [], "overall": "..." }
}
```

- `route_match`：本路与 reference 是否一致（单路视角；3 路一致性在 benchmark 层算）。
- `stuck[]`：卡壳清单，每项 `{ "type": "a" | "b", "note": "..." }`——
  `a` = 顺指针读权威源仍判不动（→ 权威源待修）；`b` = skill 该说没说（→ skill 回第 1-3 步重拆）。见 verification.md §黑箱测·重档。
- 无 `expectations` / `summary` / `claims`（无 artifact 可断言）。

## 5 · metrics.json（`<run-dir>/outputs/metrics.json`）

执行 sub-agent 自留，grader 读入并拷进 grading.json 的 `execution_metrics`。

```json
{
  "tool_calls": { "Read": 5, "Write": 2 }, "total_tool_calls": 7,
  "total_steps": 4, "files_created": 2, "errors_encountered": 0,
  "output_chars": 12450, "transcript_chars": 3200
}
```

`output_chars` 当 token 代理量（无终态时仍可量转写规模）。

## 6 · timing.json（`<run-dir>/timing.json`）

```json
{
  "total_tokens": 84852, "duration_ms": 23332, "total_duration_seconds": 23.3,
  "executor_start": "...", "executor_end": "...", "executor_duration_seconds": 165.0,
  "grader_start": "...", "grader_end": "...", "grader_duration_seconds": 26.0
}
```

执行一结束立刻写（`total_tokens` / `duration_ms` 只有此刻能拿到，过后丢失）。

---

## 7 · benchmark.json（`iteration-N/benchmark/benchmark.json`）

aggregate_benchmark.py 产出（见 `scripts/aggregate_benchmark.py`）。聚合一轮内全部 run。

```json
{
  "metadata": {
    "skill_name": "dream", "skill_path": "...", "executor_model": "claude-opus-4-8",
    "analyzer_model": "claude-opus-4-8", "timestamp": "...",
    "evals_run": 6, "runs_per_configuration": 3
  },
  "runs": [
    {
      "eval_id": 0, "eval_name": "...", "eval_type": "route_convergence",
      "configuration": "with_skill", "run_number": 1,
      "result": { "primary_metric": "convergence_rate", "route_match": true, "pass_rate": null },
      "expectations": [], "notes": []
    }
  ],
  "run_summary": {
    "with_skill":   { "pass_rate": null, "convergence_rate": 1.0, "primary_metric": "convergence_rate" },
    "without_skill":{ "pass_rate": null, "convergence_rate": 0.33, "primary_metric": "convergence_rate" },
    "delta": { "convergence_rate": 0.67 }
  },
  "notes": []
}
```

- `configuration` 必为 `with_skill` 或 `without_skill`（驱动分组，名字不可改）。with_skill 排在 baseline 前。
- `[A]` 主指标 `pass_rate`：该配置下全 run 断言通过率 mean±stddev。
- `[B]` 主指标 `convergence_rate`：同节点 3 路走同分支的比率（pass^k 一致性，见 verification.md §pass^k）+ 对 reference 的 route_match 率。
- `run_summary` 两类字段都列，按 `primary_metric` 指明本轮主看哪个；不适用的填 `null`。
- `delta` = with − without，只对主指标算。

---

## 8 · comparison.json（`iteration-N/.../comparison-N.json`，Improve 模式）`[A]` 主用

comparator agent 盲评产出（见 `agents/comparator.md`）。A/B 双盲对比两版输出，不知谁是谁。

```json
{
  "winner": "A",
  "reasoning": "为何 A 胜 / 为何 tie，引具体处",
  "rubric": {
    "A": { "content": { "correctness": 5, "completeness": 5, "accuracy": 4 },
           "structure": { "organization": 4, "formatting": 5, "usability": 4 },
           "content_score": 4.7, "structure_score": 4.3, "overall_score": 9.0 },
    "B": { "...": "同结构" }
  },
  "output_quality": { "A": { "score": 9, "strengths": [], "weaknesses": [] }, "B": { "...": "" } },
  "expectation_results": {
    "A": { "passed": 4, "total": 5, "pass_rate": 0.8, "details": [ { "text": "...", "passed": true } ] },
    "B": { "...": "" }
  }
}
```

- `winner` ∈ `A` / `B` / `TIE`；rubric 各维 1–5，overall 缩放到 1–10。
- `expectation_results` 仅 end_state 有 expectations 时出，无则整字段删。
- `[B] route_convergence 适配`：无 artifact 质量可比 → comparator 比"两版的路由正确性 + 收敛稳定性 + 卡壳少否"，rubric 维度换成 `route_correctness` / `convergence_stability` / `stuck_count`（见 comparator.md route 分支），output_quality 仍给 1–10。

## 9 · analysis.json（`iteration-N/.../analysis.json`，Improve 模式）

analyzer agent 产出（见 `agents/analyzer.md`）。揭盲后追因：赢家为何赢、输家怎么改。

```json
{
  "comparison_summary": { "winner": "A", "winner_skill": "...", "loser_skill": "...", "comparator_reasoning": "..." },
  "winner_strengths": ["..."],
  "loser_weaknesses": ["..."],
  "instruction_following": { "winner": { "score": 9, "issues": [] }, "loser": { "score": 6, "issues": ["..."] } },
  "improvement_suggestions": [
    { "priority": "high", "category": "instructions", "suggestion": "...", "expected_impact": "..." }
  ],
  "transcript_insights": { "winner_execution_pattern": "...", "loser_execution_pattern": "..." }
}
```

- `priority` ∈ `high`（可能翻转本对比胜负）/ `medium` / `low`。
- `category` ∈ `instructions` / `tools` / `examples` / `error_handling` / `structure` / `references`。

## 10 · history.json（workspace 根，Improve 模式）

版本胜负账。每跑一轮 Improve 追加一条 iteration。

```json
{
  "started_at": "...", "skill_name": "dream", "current_best": "iteration-2",
  "iterations": [
    { "version": "iteration-1", "parent": null, "eval_type": "route_convergence",
      "primary_metric": "convergence_rate", "metric_value": 0.33,
      "grading_result": "baseline", "is_current_best": false },
    { "version": "iteration-2", "parent": "iteration-1",
      "primary_metric": "convergence_rate", "metric_value": 1.0,
      "grading_result": "won", "is_current_best": true }
  ]
}
```

- `grading_result` ∈ `baseline` / `won` / `lost` / `tie`（相对 parent 或 current_best，由 comparator 定）。
- `primary_metric` / `metric_value`：本系统加，让胜负账对两类 eval 都机器可读（Anthropic 原版只有 `expectation_pass_rate`）。
- `current_best` 由 test-score（非 train）择优，防过拟合。

---

## 11 · trigger 触发 eval 数据（`trigger_eval/`，第 7 步）

### trigger_set.json — 触发用例

```json
[
  { "query": "用户可能这么说的话（口语/隐含需求）", "should_trigger": true },
  { "query": "近义但不该触发的话（near-miss：共享关键词、实则要别的）", "should_trigger": false }
]
```

- 20 条起：8-10 条 should_trigger（多样措辞 + 隐含需求 + 该赢的竞争 skill 场景）+ 8-10 条 should_not_trigger（**near-miss** 最值钱：共享关键词但需要的是别的；别放显然无关的）。
- 注意：Claude 只为"自己难独力搞定"的任务查 skill，琐碎一步任务不是好测例。

### result.json — score 产出

```json
{
  "skill_name": "dream",
  "original_description": "...",
  "best_description": "test-score 择出的最优 description",
  "best_version": "original",
  "best_test_score": 0.90,
  "runs_per_query": 3,
  "split": { "train": 0.6, "test": 0.4 },
  "method": "agent 派 sub-agent 判定（无 subprocess/CLI 依赖）",
  "iterations": [
    { "version": "original", "description": "...", "train_score": 0.7, "test_score": 0.75, "train_failures": [] }
  ]
}
```

- 60% train / 40% held-out test；每 query 由 **N 个独立 sub-agent** 各判一次取多数票（替代旧版「同 query 调 N 次 CLI」）；`best_description` 按 **test_score** 择优（非 train，防过拟合）。
- 判定不经 subprocess/CLI：由执行 meta-skill 的 agent 派 sub-agent 做，写回 `judging/<version>/run*.json`，`score` 子命令多数票计分。
- `result.json` 每次 `score` 重算（canonical 形状，自愈旧架构残留键）。方法细节见 SKILL.md 第 7 步。
