#!/usr/bin/env python3
"""Check a translated batch: python3 -I check_batch.py <batch.json> <out.json>

Uses the same SmartString/markup rules as tools/localization_tool.py validate,
plus missing/extra keys, Simplified-Chinese characters and untranslated text.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

TOOL = str(Path(__file__).resolve().parents[1] / "localization_tool.py")
spec = importlib.util.spec_from_file_location("loctool", TOOL)
loctool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loctool)

# Characters that only exist in Simplified Chinese (common in game/UI text).
SIMPLIFIED = set("这们个为说时对会么还过发样话后经现长东动战机舰击炮导弹队员级将军设载览录键标显钮档网络连线开关择确认帮务护货运输备侦报给与从门间问让应该没头见观实际边远进选达务权极几乱亚产亲众优传伤体侧储儿党兰关兴养兽决况冲减凤删别刹剧剑劳势区医华单卫压厅历县参双变叠叶号叹吗员呜响哑团园围图圆场坏块坚坛垒")


def main(batch_path, out_path):
    batch = json.load(open(batch_path, encoding="utf-8"))
    out = json.load(open(out_path, encoding="utf-8"))
    keys = {i["key"] for i in batch}
    problems, warnings = [], []
    for k in sorted(set(out) - keys):
        problems.append((k, "extra key not in batch"))
    for item in batch:
        k, src = item["key"], item["source"]
        tgt = out.get(k)
        if tgt is None or tgt == "":
            problems.append((k, "missing translation"))
            continue
        for err in loctool.check_translation(src, tgt):
            problems.append((k, err))
        bad = sorted({c for c in tgt if c in SIMPLIFIED})
        if bad:
            problems.append((k, "simplified characters: " + "".join(bad)))
        if src.count("\n") != tgt.count("\n"):
            problems.append((k, f"line breaks {src.count(chr(10))} -> {tgt.count(chr(10))}"))
        if tgt == src and re.search(r"[a-z]{3,}", src):
            warnings.append((k, "WARN identical to English source (OK only for callsigns/codes/names)"))
    for k, msg in problems + warnings:
        print(f"{k}\t{msg}")
    print(f"{len(batch)} items, {len(out)} translated, {len(problems)} error(s), {len(warnings)} warning(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
