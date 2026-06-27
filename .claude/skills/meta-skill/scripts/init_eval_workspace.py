# -*- coding: utf-8 -*-
"""
init_eval_workspace.py — meta-skill 第 8 步：搭 eval workspace 骨架。

大白话契约（给不懂代码的人看）：
  这个脚本只建文件夹 + 写空 JSON 模板，绝不调模型、绝不动 skill 文件。无外部依赖，python3 直接跑。
  Anthropic 没有这个脚本（它靠 agent 现搭目录）；本系统把它固化成脚本，省得每次手搭出错。

  两种用法：
    1) 起骨架（第一次）：
       python init_eval_workspace.py "<目标skill名>"
       → 在当前工作目录的 _meta_eval_workspace/<skill名>/ 下建 evals/ trigger_eval/ review/
         + 写 evals.json / trigger_set.json / history.json 空模板。
       （workspace 根可用 --root 改）

    2) 摊一轮 run 目录（evals.json 填好后）：
       python init_eval_workspace.py "<目标skill名>" --iteration 1
       → 读 evals/evals.json，按 eval 条数 × {with_skill, without_skill} × runs 摊出
         iteration-1/eval-K-CONFIG-runN/ 目录（含 outputs/）+ benchmark/。
       --runs N 控制每配置跑几次（默认 3，对应 pass^k 的 k）。

  数据形状见 references/schemas.md。本脚本只管目录与空壳，不填内容、不评分。
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_ROOT = os.path.join(os.getcwd(), "_meta_eval_workspace")


def _write_json(path, obj):
    """只在文件不存在时写模板，绝不覆盖已填内容。"""
    if os.path.exists(path):
        print(f"  跳过（已存在，不覆盖）: {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"  写: {path}")


def _mkdir(path):
    os.makedirs(path, exist_ok=True)
    print(f"  建: {path}")


def scaffold(ws, skill):
    """模式 1：起骨架。"""
    print(f"[起骨架] {ws}")
    _mkdir(ws)
    _mkdir(os.path.join(ws, "evals"))
    _mkdir(os.path.join(ws, "trigger_eval"))
    _mkdir(os.path.join(ws, "review"))

    _write_json(os.path.join(ws, "evals", "evals.json"), {
        "skill_name": skill,
        "evals": [
            {
                "id": 0,
                "eval_type": "end_state",
                "prompt": "（填：用户任务 prompt）",
                "files": [],
                "expected_output": "（填：期望产物描述）",
                "expectations": ["（填：可客观验证的断言）"]
            },
            {
                "id": 1,
                "eval_type": "route_convergence",
                "prompt": "（填：触发该 skill 的任务 prompt）",
                "files": [],
                "expected_route": "（填：已知正确路由）",
                "reference_solution": "（填：这条路由为何对）",
                "dry_run": True
            }
        ]
    })
    _write_json(os.path.join(ws, "trigger_eval", "trigger_set.json"), [
        {"query": "（填：该触发的用户说法）", "should_trigger": True},
        {"query": "（填：near-miss，不该触发）", "should_trigger": False}
    ])
    _write_json(os.path.join(ws, "history.json"), {
        "started_at": "",
        "skill_name": skill,
        "current_best": None,
        "iterations": []
    })
    print("[骨架完成] 下一步：手工填 evals/evals.json 与 trigger_eval/trigger_set.json，再 --iteration 1 摊 run 目录")


def lay_iteration(ws, n, runs):
    """模式 2：摊一轮 run 目录。读 evals.json 拿 eval 条数。"""
    evals_path = os.path.join(ws, "evals", "evals.json")
    if not os.path.isfile(evals_path):
        print(f"FAIL: 找不到 {evals_path}，先跑骨架模式并填好 evals.json")
        sys.exit(1)
    with open(evals_path, encoding="utf-8") as f:
        evals = json.load(f).get("evals", [])
    if not evals:
        print("FAIL: evals.json 里 evals 为空")
        sys.exit(1)

    it_dir = os.path.join(ws, f"iteration-{n}")
    print(f"[摊 iteration-{n}] {len(evals)} 条 eval × {{with,without}}_skill × {runs} 次")
    _mkdir(it_dir)
    for ev in evals:
        eid = ev.get("id")
        for config in ("with_skill", "without_skill"):
            for r in range(1, runs + 1):
                run_dir = os.path.join(it_dir, f"eval-{eid}-{config}-run{r}")
                _mkdir(os.path.join(run_dir, "outputs"))
    _mkdir(os.path.join(it_dir, "benchmark"))
    print(f"[摊完] 执行 sub-agent 把产物落进各 run 的 outputs/，转写落 transcript.md，再跑 grader → aggregate_benchmark.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", help="目标 skill 名")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="workspace 根目录")
    ap.add_argument("--iteration", type=int, default=None, help="摊第 N 轮 run 目录（省略=只起骨架）")
    ap.add_argument("--runs", type=int, default=3, help="每配置跑几次（pass^k 的 k，默认 3）")
    args = ap.parse_args()

    ws = os.path.join(args.root, args.skill)
    bar = "=" * 56
    print(bar)
    print(f"init_eval_workspace.py · {args.skill}")
    print(bar)

    if args.iteration is None:
        scaffold(ws, args.skill)
    else:
        lay_iteration(ws, args.iteration, args.runs)
    print(bar)


if __name__ == "__main__":
    main()
