# 检验方法（meta-skill 第 8 步条件下沉配方）

被 `SKILL.md §第 8 步` 引用。第 8 步前两道（机械闸 / 内部逻辑审）必跑、本体已内联 SKILL.md，不在此重复。本文件只装**按 skill 特征条件下沉**的两道配方——§指针审（skill 有 references/scripts 才下沉）+ §黑箱测·重档（skill 高 stakes 才下沉）——外加两道共用的 §grader 三类 + §来源。
正文只写「查什么 / 怎么查 / grader / 判据」，不解释为什么。黑箱骨架取自 Anthropic eval 指引（来源见文末），场景特化项标注。

## grader 三类（先判归属再选工具，能确定性就别上模型）

| grader | 工具 | 判什么 |
|---|---|---|
| Code | `validate.py` / `anchor_check.py` | 死的、确定的：字段、死链、指针存在性、阈值数值扫描 |
| LLM | 异于被测的模型当裁判，每维度独立，给 "Unknown" 出口防幻觉 | 语义：自洽、一致、命令式、路由对错 |
| Human | SME 抽检 | 校准 LLM 裁判、终裁；审慎用 |

LLM 裁判 rubric 要明确（"路由未走 reference 指定分支即 incorrect"）；让裁判先推理再打标签，然后丢弃推理只取标签。

## 指针审（第 8 步第三道下沉 · skill 有 references / scripts 才跑）

skill 引用了外部权威源时才有指针可审；纯 extract-mode 内联 skill 本道空过。逐项 pass/fail：

| 项 | 查什么 | 怎么查 | grader |
|---|---|---|---|
| 复制体 | 判据有权威源的家，却把本体内联进 skill | `anchor_check.py "<SKILL.md>" --inline` 列阈值数值候选 → 逐条查权威源有无家 → 有家而内联 = fail（改指针） | Code 筛 + Human 判 |
| 指针有效 | 引用的每个 §X 真实可达且确含所称判据 | `anchor_check.py "<SKILL.md>"` 解析每个 (文件,§) 对，到目标文件验标题存在 → DEAD/NOFILE = fail；AMBIG = 节名太泛、写到能唯一命中 | Code |
| 被引自洽 | skill 引到的权威源片段彼此不矛盾 | 只读被引片段；矛盾 = fail 且标"权威源待修"，不在审 skill 时改权威源 | LLM + Human |

边界（防 scope 爆炸）：只查被 skill 引用到的片段。发现权威源缺判据 / 不自洽 → 报告 + 标"权威源待修"，完整权威源自洽审计另起一轮。

## 黑箱测·重档（第 8 步第四道下沉 · skill 高 stakes 才跑）

skill 判错担责 / 要求接近 100% 复现率（接第 1 步 `可接受复现率`）才触发本档；否则停在第 8 步内联的轻档 smoke。重档 = 收敛测（同任务 × 3 路 + pass^k + held-out 切分），主 agent 派 sub-agent 真跑、自己只裁断（不下场试跑）。

### 任务集构造

- 目标量：**10 起步 / 30 健康 / 50 上限**。实际量由判断节点覆盖长出来（每节点 ≥1 + 边界 case 骑墙信号/临界值/分支两侧），不硬凑、不为凑数编假任务。
- 每条标 `eval_type`：有终态产物 = end_state / 不可逆无终态 = route_convergence；每条配 reference solution（已知正确路由/产物），验任务可解 + 校 grader。
- 准入：两 SME 独立判 pass/fail 得同结论才算好任务。
- 平衡集：同放"该触发"与"不该触发"两侧，防单边优化。
- 某任务 0% 全挂，先疑任务坏，非 agent 无能。

### 测试集来源（高 stakes 但无测试集时的降级链）

skill 高 stakes、本该跑重档，但手上没有现成测试集时，按序走：

1. **有案例库 / 测试集 / 校准集** → 切 held-out：旧段做蒸馏 train、新段做测试 test（与第 7 步触发 eval 同一 60/40 切分机制，从 query 层搬到 case-corpus 层）。
2. **无测试集** → 问使用者：要你提供测试集，还是我去网上检索真实任务？
   - 使用者提供 → 用使用者给的。
   - 使用者无法提供 / 令检索 → 去网上检索真实任务，拿来当测试集跑。
3. 检索也补不够 10 个 → 标红"基于 N 例、统计置信低"，按现有量跑，不编假任务凑数。

（取测试数据问使用者 / 检索，是检验层取数，不违反第 1 步"蒸馏层不向用户追问判据"——层不同。）

### 跑法

- 搭 workspace + 备任务集：`python scripts/init_eval_workspace.py "<名>"` 起骨架 → 填 `evals/evals.json`（形状见 `references/schemas.md`）→ `python scripts/init_eval_workspace.py "<名>" --iteration 1 --runs 3` 摊 run 目录。
- 派 3 路独立 sub-agent：各 clean context、互不可见、不给主 agent 结论；产物落各 run `outputs/`、转写落 `transcript.md`。
- skill 含不可逆动作（改文件 / 建 cron / 删数据）→ `eval_type=route_convergence` 且令其 DRY RUN（声明动作不真做）。
- 主轮（必跑）：可读 skill 引用的权威源 → 测指针有效。
- 判据必要性轮（按需）：不读权威源 → 三档：读了才判对 = 指针有效判据该留 / 不读也判对 = 可能已被模型默认吸收、可议删 / 读了仍判不动 = 指针错或权威源缺判据。
- 派 grader sub-agent 评分（prompt 见 `agents/grader.md`）：逐 run 写 `grading.json`（end_state 评断言 / route_convergence 评路由 + 卡壳清单 (a)(b)）。
- 聚合：`python scripts/aggregate_benchmark.py "<ws>/iteration-1" --skill-name <名>` → benchmark.json/.md（end_state 主指标 pass_rate / route_convergence 主指标 convergence_rate）。
- 生成人审 HTML：`python eval-viewer/generate_review.py "<ws>/iteration-1" --skill-name <名> --static <out.html>` → 交人审。

### 主 agent 裁断（不下场试跑，只据报告 + 人审反馈）

- 收敛判定：同节点 3 路走同分支 = 收敛；用 pass^k（要一致性，非 pass@k）。
- 拿 reference solution 给路由/产物做 code grade，防 3 路集体滑到同一错。
- 分叉追因：卡壳 (a) → 权威源补判据（标"权威源待修"，非本流程改）；(b) → skill 回第 1-3 步重拆。
- 必读 transcript：分清是 skill 错，还是 grader 拒了合法解。

### pass^k vs pass@k

- pass@k = k 次至少 1 次对（随 k 升）；用于"一次成功就够"（如 coding）。
- pass^k = k 次全对（随 k 降；单次 75%、跑 3 次 ≈ 42%）；用于"要一致性"。
- 本场景用 pass^k：skill 作协议，要稳定可复现，不是偶尔跑对。
- 环境隔离：每次试验 clean context，防共享 state 致相关性失败。

### 阈值

- 改进型 eval（skill 未上线）：起步可低通过率，留爬坡空间。
- 回归型 eval（skill 已上线）：须接近 100%，任何下滑即破坏信号。
- 不按字面信分数：必读 transcript 确认评分公平。
- 饱和：可解任务全过、无提升空间 = 饱和；capability eval 优化到高通过后可"毕业"成持续回归套件。

### DRY-RUN 场景特化

不可逆 skill（动记忆池 / 建 cron / 删数据）无真实终态 → 主指标改为路由收敛性（3 路同节点是否走同分支）+ reference solution 对路由结论做 code grade。评终态 / 路由，不评说辞、不评 tool-call 序列（序列太脆，agent 会找合理意外解）。多组件任务用 partial credit。

## 脚本（索引 · 详细参数见各步就地引用）

- `scripts/validate.py "<skill 文件夹>"` — 机械闸 M1-M5（frontmatter / 必填字段 / 死链 / 杂物 / description）。随 skill 文件夹携带（promote 时一并复制到 `~/.claude/skills/<名>/scripts/`）。
- `scripts/anchor_check.py "<SKILL.md>" [--inline]` — 指针审：默认解析指针有效性；`--inline` 加复制体阈值数值候选扫描。
- `scripts/init_eval_workspace.py "<名>" [--iteration N] [--runs K]` — 搭 eval workspace 骨架 / 摊 run 目录。只建目录写空模板，不调模型。
- `scripts/run_trigger_eval.py prepare / score` — 第 7 步触发 eval（prepare 切分+判定卡 / score 多数票计分，均不调模型、无 subprocess/CLI 依赖）。
- `scripts/aggregate_benchmark.py "<ws>/iteration-N" --skill-name <名>` — 聚合 grading → benchmark.json/.md，指标按 eval_type 分流。
- `eval-viewer/generate_review.py "<ws>/iteration-N" --skill-name <名> --static <out>` — 人审 HTML（静态态，单机不守 server）；`--trigger` 切触发 eval 复核模式。
- agent prompt：`agents/grader.md`（评分）/ `agents/comparator.md`（盲评，第 9 步）/ `agents/analyzer.md`（追因，第 9 步）。
- eval workspace 数据形状全在 `references/schemas.md`。

## 来源

Anthropic 官方 eval 方法学（2026 口径）：
- 《Demystifying evals for AI agents》— anthropic.com/engineering/demystifying-evals-for-ai-agents（构集 / grading / pass@k vs pass^k / 评终态 / 阈值）
- 《Define success criteria and build evaluations》— platform.claude.com/docs（SMART 标准 / edge case / LLM rubric）
- 《Building evals》Cookbook — platform.claude.com/cookbook（grader 代码模板 + 裁判 prompt 结构）
- 《Improving skill-creator: Test, measure, refine》— claude.com/blog（benchmark 三指标 / Comparator 盲评 A/B / "base 模型也过 = skill 可退役"信号）

场景特化（本系统加，非 Anthropic）：路由收敛性主指标（因 DRY RUN 无终态）/ 读不读权威源筛判据必要性 / 卡壳 (a)(b) 分类 / 3 路对齐记忆系统三路独立蒸馏 / 轻档 smoke 地板 + 重档收敛条件触发 / 测试集来源降级链（问使用者→检索）/ 10-30-50 量纲。
