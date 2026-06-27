# -*- coding: utf-8 -*-
"""
aggregate_benchmark.py — meta-skill 第 8 步：聚合一轮 run 的评分 → benchmark。

大白话契约（给不懂代码的人看）：
  grader 给每个 run 写了 grading.json 之后，这个脚本把一整轮（iteration-N）的所有 run 收起来，
  按 with_skill / without_skill 分组算总分，产出 benchmark.json + benchmark.md（人看的对照表）。
  它只读 grading.json、只写 benchmark.*，不调模型、不动 skill。无外部依赖。

  逻辑照搬 Anthropic aggregate_benchmark；指标按 eval_type 分流（本系统加）：
    end_state         → pass_rate（断言通过率）
    route_convergence → convergence_rate（同 eval 同配置下 route_match 的 run 占比，即 pass^k 一致性）

  用法：
    python aggregate_benchmark.py "<workspace>/iteration-N" --skill-name <name> [--model <id>]

  run 目录命名：eval-{id}-{config}-run{n}/  （init_eval_workspace.py 摊出）
  每个 run 里要有 grading.json（grader 产出）。缺的标 missing，不算分。

  数据形状见 references/schemas.md §7。
"""
import argparse
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RUN_RE = re.compile(r"^eval-(?P<eid>\d+)-(?P<config>with_skill|without_skill)-run(?P<run>\d+)$")


def load_grading(run_dir):
    p = os.path.join(run_dir, "grading.json")
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [坏 grading.json] {p}: {e}")
        return None


def run_metric(g):
    """从一个 grading.json 取 (eval_type, 主指标值 0..1 或 None)。"""
    et = g.get("eval_type")
    if et == "end_state":
        return et, g.get("summary", {}).get("pass_rate")
    if et == "route_convergence":
        rr = g.get("route_result", {})
        return et, (1.0 if rr.get("route_match") else 0.0)
    return et, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iteration_dir")
    ap.add_argument("--skill-name", required=True)
    ap.add_argument("--model", default="")
    args = ap.parse_args()

    it_dir = args.iteration_dir
    if not os.path.isdir(it_dir):
        print(f"FAIL: 不是目录 {it_dir}")
        sys.exit(1)

    bar = "=" * 56
    print(bar); print(f"aggregate_benchmark.py · {args.skill_name} · {os.path.basename(it_dir)}"); print(bar)

    runs = []          # 扁平 run 记录
    # 分组：by (eval_id, config) 收集主指标，算每 eval 的 convergence / pass
    by_eval_cfg = defaultdict(list)   # (eid, config) -> [metric...]
    eval_types = {}                   # eid -> eval_type

    for name in sorted(os.listdir(it_dir)):
        m = RUN_RE.match(name)
        if not m:
            continue
        eid = int(m.group("eid")); config = m.group("config"); rn = int(m.group("run"))
        g = load_grading(os.path.join(it_dir, name))
        if g is None:
            runs.append({"eval_id": eid, "configuration": config, "run_number": rn,
                        "result": {"missing": True}})
            continue
        et, metric = run_metric(g)
        eval_types[eid] = et
        by_eval_cfg[(eid, config)].append(metric if metric is not None else 0.0)
        runs.append({
            "eval_id": eid,
            "eval_name": g.get("route_result", {}).get("expected_route", "") if et == "route_convergence" else "",
            "eval_type": et, "configuration": config, "run_number": rn,
            "result": {
                "primary_metric": "convergence_rate" if et == "route_convergence" else "pass_rate",
                "route_match": g.get("route_result", {}).get("route_match") if et == "route_convergence" else None,
                "pass_rate": g.get("summary", {}).get("pass_rate") if et == "end_state" else None,
            },
            "expectations": g.get("expectations", []),
            "notes": [s.get("note", "") for s in g.get("route_result", {}).get("stuck", [])],
        })

    if not runs:
        print("FAIL: 该 iteration 下没有 eval-*-run* 目录（先跑 init_eval_workspace.py --iteration N）")
        sys.exit(1)

    # 每配置汇总：把每个 (eval,config) 的多 run 主指标先取均值（= 该 eval 在该配置下的一致性/通过率），
    # 再对所有 eval 取均值得该配置总分。
    def summarize(config):
        per_eval = []
        for (eid, cfg), vals in by_eval_cfg.items():
            if cfg != config or not vals:
                continue
            per_eval.append(statistics.mean(vals))
        if not per_eval:
            return {"pass_rate": None, "convergence_rate": None, "primary_metric": None}
        score = statistics.mean(per_eval)
        # 本轮主指标看是否有 route_convergence 类
        has_route = any(eval_types.get(eid) == "route_convergence" for (eid, c) in by_eval_cfg if c == config)
        primary = "convergence_rate" if has_route else "pass_rate"
        return {
            "pass_rate": round(score, 3) if primary == "pass_rate" else None,
            "convergence_rate": round(score, 3) if primary == "convergence_rate" else None,
            "primary_metric": primary,
        }

    with_s = summarize("with_skill")
    without_s = summarize("without_skill")
    primary = with_s.get("primary_metric") or without_s.get("primary_metric") or "pass_rate"
    w = with_s.get(primary); wo = without_s.get(primary)
    delta = round((w - wo), 3) if (w is not None and wo is not None) else None

    n_evals = len(set(r["eval_id"] for r in runs))  # 数所有摊出的 eval（含缺 grading 的 missing），不只有评分的
    runs_per = max((r["run_number"] for r in runs if "run_number" in r), default=0)

    benchmark = {
        "metadata": {
            "skill_name": args.skill_name, "skill_path": "", "executor_model": args.model,
            "analyzer_model": args.model, "timestamp": datetime.now().isoformat(timespec="seconds"),
            "evals_run": n_evals, "runs_per_configuration": runs_per,
        },
        "runs": runs,
        "run_summary": {
            "with_skill": with_s, "without_skill": without_s,
            "delta": {primary: delta},
        },
        "notes": [],
    }

    out_json = os.path.join(it_dir, "benchmark", "benchmark.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(benchmark, f, ensure_ascii=False, indent=2)

    # 人看的 md
    lines = [
        f"# benchmark · {args.skill_name} · {os.path.basename(it_dir)}",
        "",
        f"主指标: **{primary}**  ·  evals={n_evals}  ·  runs/配置={runs_per}",
        "",
        "| 配置 | 主指标值 |",
        "|---|---|",
        f"| with_skill | {with_s.get(primary)} |",
        f"| without_skill | {without_s.get(primary)} |",
        f"| **delta (with − without)** | **{delta}** |",
        "",
        "## 逐 run",
        "",
        "| eval | config | run | route_match / pass_rate |",
        "|---|---|---|---|",
    ]
    for r in runs:
        res = r["result"]
        val = res.get("route_match") if res.get("primary_metric") == "convergence_rate" else res.get("pass_rate")
        if res.get("missing"):
            val = "MISSING"
        lines.append(f"| {r['eval_id']} | {r.get('configuration')} | {r.get('run_number')} | {val} |")
    out_md = os.path.join(it_dir, "benchmark", "benchmark.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"主指标 {primary}:  with={w}  without={wo}  delta={delta}")
    print(f"写: {out_json}")
    print(f"写: {out_md}")
    print(bar)


if __name__ == "__main__":
    main()
