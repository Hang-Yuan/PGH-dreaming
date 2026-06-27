# -*- coding: utf-8 -*-
"""
validate.py — meta-skill 的机械层审计器。

大白话契约（给不懂代码的人看）：
  这个脚本只查"死的、确定的"东西，不做任何需要判断的事。
  用法：  python validate.py "<skill 文件夹路径>"
  例如：  python validate.py "~/.claude/skills/daily-review"
  它会读这个文件夹里的 SKILL.md，跑 5 项检查，打印 PASS/FAIL 报告。
  全 PASS → 退出码 0；有 FAIL → 退出码 1。
  它绝不修改任何文件，只读 + 打印。无任何外部依赖，python 3 直接跑。

  五项检查：
    M1 frontmatter 能解析（开头 --- 紧跟 name:，中间没有空行）
    M2 必填字段齐：name / description / updated
    M3 死链：正文里写到的本地文件路径，文件真的存在吗（§ 节锚点只列出来给人工抽查）
    M4 杂物：文件夹里有没有孤儿文件 / 残留备份（.bak、副本、~ 结尾、_old、备份 等）
    M5 description 非空、且不长到不像触发句（>600 字提醒）
"""
import os
import re
import sys

# Windows 控制台默认 GBK，强制 UTF-8 输出，避免中文报告变乱码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def load_skill_md(folder):
    p = os.path.join(folder, "SKILL.md")
    if not os.path.isfile(p):
        return None, p
    with open(p, encoding="utf-8") as f:
        return f.read(), p


def check_frontmatter(text):
    """返回 (fail 列表, 解析出的 meta dict)。覆盖 M1。"""
    fails = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ["M1 FAIL: 文件没有以 --- 开头的 frontmatter"], {}
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return ["M1 FAIL: frontmatter 没有闭合的 ---"], {}
    if lines[1].strip() == "":
        fails.append("M1 FAIL: 开头 --- 和第一个字段之间有空行（YAML 会读不到字段）")
    meta = {}
    for i in range(1, close):
        line = lines[i]
        if line.strip() == "":
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return fails, meta


def main():
    if len(sys.argv) < 2:
        print('用法: python validate.py "<skill 文件夹路径>"')
        sys.exit(2)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"FAIL: 路径不是文件夹: {folder}")
        sys.exit(2)

    text, mdpath = load_skill_md(folder)
    if text is None:
        print(f"FAIL: 找不到 {mdpath}")
        sys.exit(1)

    report = []
    ok = True

    # M1 + frontmatter 解析
    fm_fails, meta = check_frontmatter(text)
    if fm_fails:
        report.extend(fm_fails)
        ok = False
    else:
        report.append("M1 PASS: frontmatter 结构正常")

    # M2 必填字段
    required = ["name", "description", "updated"]
    missing = [k for k in required if k not in meta or meta[k] == ""]
    if missing:
        report.append(f"M2 FAIL: 缺字段 {missing}")
        ok = False
    else:
        report.append("M2 PASS: name/description/updated 齐")

    # M5 description
    desc = meta.get("description", "")
    if not desc:
        report.append("M5 FAIL: description 空")
        ok = False
    elif len(desc) > 600:
        report.append(f"M5 WARN: description {len(desc)} 字，偏长——确认它是触发句不是摘要")
    else:
        report.append(f"M5 PASS: description {len(desc)} 字")

    # M3 死链：抓 Windows 绝对路径。允许目录名含空格 / 中文（"Meta Zone"、"01 Projects"），
    # 靠扩展名 / 尾反斜杠锚定 + 前瞻边界，避免空格截断误判（旧版 \s 截断 bug）。
    path_re = re.compile(
        r"[A-Za-z]:\\"
        r"[^\r\n`\"<>|*?]*?"
        r"(?:\.(?:md|py|json|html|txt|csv|ya?ml|ps1|bat|ini|cfg|toml)|\\)"
        r"(?=[\s`\"，。；、）)」』,;]|$)"
    )
    paths = path_re.findall(text)
    dead = []
    for p in sorted(set(paths)):
        p2 = p.rstrip(".·、")
        if not os.path.exists(p2):
            dead.append(p2)
    if dead:
        report.append("M3 FAIL: 下列路径不存在（死链）:")
        for d in dead:
            report.append(f"        {d}")
        ok = False
    else:
        report.append("M3 PASS: 正文里的本地文件路径都存在")
    anchors = sorted(set(re.findall(r"§[^\s`，,。；;）)」』]+", text)))
    if anchors:
        shown = anchors[:8]
        tail = " ..." if len(anchors) > 8 else ""
        report.append(f"M3 NOTE: {len(anchors)} 个 § 节锚点脚本不验，人工抽查: {shown}{tail}")

    # M4 杂物
    allowed_top = {"SKILL.md", "scripts", "references", "agents", "assets", "eval-viewer"}
    junk = []
    for name in sorted(os.listdir(folder)):
        if name in allowed_top:
            continue
        if re.search(r"(\.bak$|~$|\bcopy\b|副本|_old|备份)", name, re.I):
            junk.append(name + "（疑似残留备份）")
        else:
            junk.append(name + "（非标准条目，确认是否该在）")
    if junk:
        report.append("M4 WARN: 文件夹里有非标准条目:")
        for j in junk:
            report.append(f"        {j}")
    else:
        report.append("M4 PASS: 文件夹干净")

    bar = "=" * 56
    print(bar)
    print(f"validate.py 机械层报告 · {folder}")
    print(bar)
    for r in report:
        print(r)
    print(bar)
    print("结论:", "全部机械检查通过 [OK]" if ok else "有 FAIL，先修机械层再进判断层 [X]")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
