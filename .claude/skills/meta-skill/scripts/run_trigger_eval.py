# -*- coding: utf-8 -*-
"""
run_trigger_eval.py — meta-skill 第 7 步：description 触发 eval（agent 派 sub-agent 判定版）。

大白话契约（给不懂代码的人看）：
  这个脚本测一件事——skill 的 description 写得好不好，能不能让模型在「该用」时
  想起调它、在「不该用」时不误触发。

  关键修复（2026-06-26）：旧版用 subprocess 起一个新的 claude CLI 子进程当判定器，
  那个子进程不继承登录态 → `Not logged in` 卡死，且换机/换登录态结果就变、不可复现。
  本版彻底去掉 subprocess：**判定由执行 meta-skill 的 agent 派 sub-agent 做**
  （与第 5、8 步同一套路），脚本只干两件确定性的活——切分(prepare) 和 计分(score)。

  分工（见 references/verification.md §触发 eval）：
    切分 / 计分 / 择优 = Code（本脚本）；触发判定 / description 改写 / 迭代 = agent + sub-agent。

  两个子命令：
    1) prepare  读 trigger_set.json + 目标 description，60/40 切 train/test（固定 seed 可复现），
                写 _split.json + _judge_card.md（给 agent 派判定 sub-agent 的现成卡）。
    2) score    读 agent 写回的 judging/<version>/run*.json 判定，多数票计分，
                算 train/test 分 + 失败清单，更新 result.json（按 test 分择优，防过拟合）。

  用法：
    python run_trigger_eval.py prepare --skill "<名>" --skill-path "<新skill文件夹>" \\
        [--root <ws根>] [--runs 3] [--seed 42] [--version original] [--rev-desc "改写后的description"]
    python run_trigger_eval.py score   --skill "<名>" [--root <ws根>] [--version original]

  安全：只读 skill 文件、只读写 workspace/trigger_eval 下的 _split/_judge_card/judging/result；不改 skill。
"""
import argparse
import json
import os
import random
import re
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_ROOT = os.path.join(os.getcwd(), "_meta_eval_workspace")

def read_description(skill_root, skill_path=None):
    """从 skill 的 SKILL.md frontmatter 抽 description。
    优先 --skill-path 显式指定；否则现役 C 盘 → _ship → workspace 回退探测。"""
    candidates = []
    if skill_path:
        candidates.append(skill_path if skill_path.lower().endswith(".md")
                          else os.path.join(skill_path, "SKILL.md"))
    candidates += [
        os.path.join(os.path.expanduser("~"), ".claude", "skills", os.path.basename(skill_root), "SKILL.md"),
        os.path.join(skill_root, "SKILL.md"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                text = f.read()
            m = re.search(r"^description:\s*(.+)$", text, re.M)
            if m:
                return m.group(1).strip(), p
    return None, None


def load_trigger_set(ws):
    tset_path = os.path.join(ws, "trigger_eval", "trigger_set.json")
    if not os.path.isfile(tset_path):
        print(f"FAIL: 找不到 {tset_path}（先跑 init_eval_workspace.py 起骨架并填 trigger_set）")
        sys.exit(1)
    with open(tset_path, encoding="utf-8") as f:
        tset = json.load(f)
    # 给每条配稳定 id（按原始顺序），判定/计分都靠它对齐
    for i, q in enumerate(tset):
        q.setdefault("id", i)
    return tset


def split_train_test(tset, seed):
    """60/40 切，固定 seed 可复现。返回 (train_ids, test_ids)。"""
    rng = random.Random(seed)
    idx = [q["id"] for q in tset]
    rng.shuffle(idx)
    cut = max(1, int(len(idx) * 0.6))
    train = idx[:cut]
    test = idx[cut:] or train  # 太小时 test 回退用 train
    return train, test

JUDGE_CARD_TMPL = """# 触发判定卡 · {skill} · 版本「{version}」

> 本卡由 `run_trigger_eval.py prepare` 生成。执行 meta-skill 的 agent 据此**派 {runs} 个独立 sub-agent**
> 各自判定全部用例，把判定写回 `judging/{version}/run1.json … run{runs}.json`，再跑 `score`。
> {runs} 个 sub-agent 互不可见、各 clean context——多数票消模型噪声（替代旧版「同 query 调 3 次」）。

## 派给每个 sub-agent 的 prompt（原样用）

你是 skill 路由判定器。下面给你一个 skill 的 description 和一组用户消息。
对每一句，只判断：面对它，模型是否应当调用这个 skill。
逐条输出 JSON，不要解释。

[skill description]
{desc}

[待判用例]（按 id）
{query_block}

只输出这个形状的 JSON（decision 取 TRIGGER 或 SKIP）：
{{"run": <本次第几个 sub-agent，1..{runs}>, "verdicts": [{{"id": 0, "decision": "TRIGGER"}}, ...]}}

## 写回落点
- `{judging_dir}\\run1.json` … `run{runs}.json`（每个 sub-agent 一份）
- 全部写完后：`python run_trigger_eval.py score --skill "{skill}" --version {version}`
"""


def cmd_prepare(args):
    ws = os.path.join(args.root, args.skill)
    tset = load_trigger_set(ws)
    if args.rev_desc:
        desc, desc_src = args.rev_desc, "(--rev-desc 改写版)"
    else:
        desc, desc_src = read_description(ws, args.skill_path)
        if not desc:
            print(f"FAIL: 读不到 {args.skill} 的 description（蒸馏中的新 skill 传 --skill-path）")
            sys.exit(1)
    train, test = split_train_test(tset, args.seed)
    teval = os.path.join(ws, "trigger_eval")
    judging_dir = os.path.join(teval, "judging", args.version)
    os.makedirs(judging_dir, exist_ok=True)
    split = {"version": args.version, "description": desc, "description_src": desc_src,
             "train_ids": train, "test_ids": test, "runs": args.runs, "seed": args.seed,
             "split": {"train": 0.6, "test": 0.4}}
    with open(os.path.join(teval, "_split.json"), "w", encoding="utf-8") as f:
        json.dump(split, f, ensure_ascii=False, indent=2)
    query_block = "\n".join(f'  {{"id": {q["id"]}}}  ← {q["query"]}' for q in tset)
    card = JUDGE_CARD_TMPL.format(skill=args.skill, version=args.version, runs=args.runs,
                                  desc=desc, query_block=query_block, judging_dir=judging_dir)
    with open(os.path.join(teval, "_judge_card.md"), "w", encoding="utf-8") as f:
        f.write(card)
    print(f"[prepare] desc 源: {desc_src}")
    print(f"[prepare] {len(tset)} 用例 → train {len(train)} / test {len(test)}（seed={args.seed}）")
    print(f"[prepare] 判定卡: {os.path.join(teval, '_judge_card.md')}")
    print(f"[prepare] 下一步：agent 派 {args.runs} 个 sub-agent 判定 → 写 {judging_dir}\\run*.json → score")

def _majority(decisions):
    """一组 TRIGGER/SKIP 取多数票；返回 True(触发)/False/None(无有效票)。"""
    fire = sum(1 for d in decisions if str(d).upper() == "TRIGGER")
    skip = sum(1 for d in decisions if str(d).upper() == "SKIP")
    if fire + skip == 0:
        return None
    return fire > skip


def _score_ids(tset_by_id, ids, votes):
    """对一组 query id：多数票 vs should_trigger，返回 (分数, 失败清单)。"""
    passed, failures = 0, []
    for qid in ids:
        q = tset_by_id[qid]
        fired = _majority(votes.get(qid, []))
        if fired is None:
            failures.append({"id": qid, "query": q["query"],
                             "should_trigger": q["should_trigger"], "fired": None})
            continue
        if fired == q["should_trigger"]:
            passed += 1
        else:
            failures.append({"id": qid, "query": q["query"],
                             "should_trigger": q["should_trigger"], "fired": fired})
    return (passed / len(ids) if ids else 0.0), failures


def cmd_score(args):
    ws = os.path.join(args.root, args.skill)
    teval = os.path.join(ws, "trigger_eval")
    split_path = os.path.join(teval, "_split.json")
    if not os.path.isfile(split_path):
        print(f"FAIL: 找不到 {split_path}（先跑 prepare）"); sys.exit(1)
    with open(split_path, encoding="utf-8") as f:
        sp = json.load(f)
    if sp.get("version") != args.version:
        print(f"FAIL: _split.json 是版本「{sp.get('version')}」，与 --version {args.version} 不符（重跑 prepare）")
        sys.exit(1)
    tset = load_trigger_set(ws)
    tset_by_id = {q["id"]: q for q in tset}
    judging_dir = os.path.join(teval, "judging", args.version)
    run_files = sorted(f for f in os.listdir(judging_dir) if re.match(r"run\d+\.json$", f)) \
        if os.path.isdir(judging_dir) else []
    if not run_files:
        print(f"FAIL: {judging_dir} 下没有 run*.json（agent 派 sub-agent 判定后才有）"); sys.exit(1)
    # 汇总各 run 的判定到 votes[id] = [decision, ...]
    votes, bad = {}, []
    for rf in run_files:
        with open(os.path.join(judging_dir, rf), encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                bad.append(f"{rf}: {e}"); continue
        for v in data.get("verdicts", []):
            votes.setdefault(v.get("id"), []).append(v.get("decision"))
    if bad:
        print("WARN 坏判定文件:", "; ".join(bad))
    tr_score, tr_fail = _score_ids(tset_by_id, sp["train_ids"], votes)
    te_score, te_fail = _score_ids(tset_by_id, sp["test_ids"], votes)
    print(f"[score] 版本「{args.version}」  {len(run_files)} 个 sub-agent 判定")
    print(f"[score] train={tr_score:.2f} ({len(tr_fail)} 失败) / test={te_score:.2f} ({len(te_fail)} 失败)")
    for f in tr_fail + te_fail:
        print(f"  ✗ id{f['id']} 应{'触发' if f['should_trigger'] else '不触发'} 实测{f['fired']}: {f['query'][:48]}")
    _update_result(teval, sp, args.version, tr_score, te_score, tr_fail)

def _update_result(teval, sp, version, tr_score, te_score, tr_fail):
    """累积写 result.json（canonical 形状）：记每版本 train/test，按 test 分择优（防过拟合）。
    只从旧文件继承 iterations，其余字段全重算——自愈掉旧架构残留的过时键（如 blocked/selftest_command）。"""
    res_path = os.path.join(teval, "result.json")
    old_iters = []
    if os.path.isfile(res_path):
        try:
            with open(res_path, encoding="utf-8") as f:
                old_iters = json.load(f).get("iterations", [])
        except Exception:
            old_iters = []
    # 同版本重跑则覆盖，再追加本轮
    iters = [it for it in old_iters if it.get("version") != version]
    iters.append({
        "version": version, "description": sp["description"],
        "train_score": tr_score, "test_score": te_score,
        "train_failures": [{"id": f["id"], "query": f["query"],
                            "should_trigger": f["should_trigger"]} for f in tr_fail],
        "scored_at": datetime.now().isoformat(timespec="seconds"),
    })
    # best 跨全部 iterations 重算（幂等：重新计分也得对的 best）
    best = max(iters, key=lambda it: (it.get("test_score") or -1.0))
    orig = next((it["description"] for it in iters if it["version"] == "original"), None)
    res = {
        "skill_name": os.path.basename(os.path.dirname(teval)),
        "original_description": orig,
        "best_description": best["description"],
        "best_version": best["version"],
        "best_test_score": best.get("test_score"),
        "runs_per_query": sp.get("runs"),
        "split": sp.get("split", {"train": 0.6, "test": 0.4}),
        "method": "agent 派 sub-agent 判定（无 subprocess/CLI 依赖）",
        "iterations": iters,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"[score] 写 {res_path}  | 当前最佳：版本「{res['best_version']}」 test={res['best_test_score']:.2f}")
    if res["best_description"] and res["best_description"] != res.get("original_description"):
        print("  ↓ best_description 与原始不同——交人确认后替换 frontmatter（脚本不自动改 skill）")



def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("prepare", help="切分 + 生成判定卡")
    pp.add_argument("--skill", required=True)
    pp.add_argument("--root", default=DEFAULT_ROOT)
    pp.add_argument("--skill-path", default=None,
                    help="被测 skill 的 SKILL.md 或其文件夹（不在 C 盘时必传）")
    pp.add_argument("--runs", type=int, default=3, help="派几个独立 sub-agent 判定")
    pp.add_argument("--seed", type=int, default=42)
    pp.add_argument("--version", default="original", help="本轮版本名（original / rev1 …）")
    pp.add_argument("--rev-desc", default=None, help="迭代时测改写后的 description（不读 SKILL.md）")
    pp.set_defaults(func=cmd_prepare)
    sp = sub.add_parser("score", help="读 sub-agent 判定计分")
    sp.add_argument("--skill", required=True)
    sp.add_argument("--root", default=DEFAULT_ROOT)
    sp.add_argument("--version", default="original")
    sp.set_defaults(func=cmd_score)
    args = ap.parse_args()
    bar = "=" * 56
    print(bar); print(f"run_trigger_eval.py {args.cmd} · {args.skill}"); print(bar)
    args.func(args)
    print(bar)


if __name__ == "__main__":
    main()



