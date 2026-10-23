import json, glob, hashlib, sys
from pathlib import Path
R, W = Path(sys.argv[1]), Path(sys.argv[2])
def key_of(s): return "m:" + hashlib.sha1(s.encode()).hexdigest()[:12]
batches = {}
def add(name, item): batches.setdefault(name, []).append(item)

# Mission/original-game text: dedupe by exact source string.
seen = {}
for p in sorted(glob.glob(str(R / "translate/03_original_game/*.json"))):
    for e in json.load(open(p, encoding="utf-8"))["entries"]:
        if not e["requires_translation"] or not e["source"].strip(): continue
        s = e["source"]; k = key_of(s)
        if k in seen: seen[k]["count"] += 1; continue
        item = {"key": k, "source": s, "context": e["context"], "notes": e["notes"], "count": 1}
        seen[k] = item
shorts = [i for i in seen.values() if len(i["source"]) <= 40]
longs = [i for i in seen.values() if len(i["source"]) > 40]
for i in shorts: add("M0_short_labels", i)
# Split long mission text into ~6 batches of similar size, keeping original order.
total = sum(len(i["source"]) for i in longs); n = 6; acc = 0; idx = 1
for i in longs:
    if acc > total * idx / n: idx += 1
    add(f"M{idx}_mission_text", i); acc += len(i["source"])

def per_entry(name, pattern):
    for p in sorted(glob.glob(str(R / pattern))):
        for e in json.load(open(p, encoding="utf-8"))["entries"]:
            if not e["requires_translation"] or not e["source"].strip(): continue
            item = {"key": e["id"], "source": e["source"], "context": e["context"], "notes": e["notes"]}
            if "field" in e: item["field"] = e["field"]
            add(name, item)
per_entry("U1_escmenu", "translate/01_ui_and_xwing/XWVM.UI.EscMenu.xliff.json")
for p in ["XWVM.Core.Games", "XWVM.UI.GameLibrary", "XWVM.xwing.ClipSubtitles", "XWVM.xwing.Concourse",
          "XWVM.xwing.PilotLogMerits", "XWVM.xwing.Tips", "XWVM.xwing.TourNames"]:
    per_entry("U2_ui_common", f"translate/01_ui_and_xwing/{p}.xliff.json")
per_entry("U2_ui_common", "translate/02_common/*.json")
per_entry("U3_smart_species", "translate/04_smart_strings/*.json")
per_entry("U3_smart_species", "translate/05_species/*.json")

for name, items in sorted(batches.items()):
    json.dump(items, open(W / "batches" / f"{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{name:22s} {len(items):5d} items {sum(len(i['source']) for i in items):7d} chars")
