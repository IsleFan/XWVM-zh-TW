#!/usr/bin/env python3
"""Write batch outputs (out/*.json) into the translate/*.json target fields (target_<locale>, e.g. target_zh_TW).

python3 -I merge_outputs.py <resources root> <work dir> [--dry-run]
Original-game entries use the deduplicated "m:<sha1>" keys; everything else uses the entry id.
"""
import glob
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

root, work = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("loctool", root / "tools" / "localization_tool.py")
loctool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loctool)
dry = "--dry-run" in sys.argv
out = {}
for p in sorted(glob.glob(str(work / "out" / "*.json"))):
    out.update(json.load(open(p, encoding="utf-8")))

filled = missing = 0
for p in sorted(glob.glob(str(root / "translate" / "*" / "*.json"))):
    doc = json.load(open(p, encoding="utf-8"))
    field = loctool.target_field(doc["target_locale"])
    for e in doc["entries"]:
        if not e["requires_translation"] or not e["source"].strip():
            continue
        key = e["id"]
        if "/03_original_game/" in p.replace("\\", "/"):
            key = "m:" + hashlib.sha1(e["source"].encode()).hexdigest()[:12]
        tgt = out.get(key)
        if tgt:
            e[field] = tgt
            filled += 1
        else:
            missing += 1
    if not dry:
        Path(p).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"filled {filled}, missing {missing}{' (dry run)' if dry else ''}")
