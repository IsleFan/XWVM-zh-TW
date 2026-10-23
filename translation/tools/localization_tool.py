#!/usr/bin/env python3
"""Offline XWVM translation workspace tools. Python standard library only.

Never executes game binaries, PowerShell scripts, or network requests.
Native export is a review candidate, not a verified installed language pack.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

NS = "urn:oasis:names:tc:xliff:document:2.0"
ET.register_namespace("", NS)
N = {"x": NS}
FIELDS = ["ABBR", "ONE", "FEW", "MANY", "OTHER", "CLASSIFIER", "DEFINITE_ART"]
DEFAULT_SOURCE = Path("/Library/Application Support/XWVM Team/XWVM/StreamingAssets/Localization")
_HERE = Path(__file__).resolve().parent
DEFAULT_OUT = _HERE.parent if _HERE.name == "tools" else _HERE / "XWVM-zh-TW-translation-resources"
DEFAULT_LOCALE = "zh-TW"

# Plural branch counts required by Unity Localization's SmartFormat rules (PluralRules), per language.
# Languages with a single form always use the first branch, so every branch must be the general form.
SINGLE_FORM_LANGUAGES = set("az bm bo dz fa hu id ig ii ja jv ka kde kea km kn ko ms my root sah ses sg th to vi wo yo zh".split())
PLURAL_FORMS = {**{l: 3 for l in "be bs cs ga hr iu ksh kw lag lt lv mo ro ru se sh shi sk sma smi smj smn sms sr uk".split()},
                **{l: 4 for l in "mt pl sl".split()},
                **{l: 6 for l in "ar br cy".split()}}


def target_field(locale):
    """Workspace field holding the translation, e.g. zh-TW -> target_zh_TW, ja -> target_ja."""
    if not re.fullmatch(r"[a-z]{2}(-[A-Z]{2})?", locale):
        raise ValueError("語系代碼格式須為 xx 或 xx-YY（XWVM 只認得這種檔名），例如 ja、ko、zh-TW：" + locale)
    return "target_" + locale.replace("-", "_")


def language_of(locale):
    return locale.split("-")[0].lower()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(path):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.parse(path, parser=parser)


def inner(node):
    if node is None:
        return ""
    if not len(node):
        return node.text or ""
    chunks = [node.text or ""]
    for child in node:
        text = ET.tostring(child, encoding="unicode")
        chunks.append(text.replace(' xmlns="' + NS + '"', ""))
    return "".join(chunks)


def canonical_name(name):
    return name.replace("_es.", ".").replace("_en.", ".")


def category(name):
    if "OriginalStrings" in name:
        return "03_original_game"
    if any(s in name for s in ["CombatVocab", "TriggersAndGoals", "Hangar", "PlayerActions"]):
        return "04_smart_strings"
    if ".Common." in name:
        return "02_common"
    return "01_ui_and_xwing"


def make_document(path, relative, locale=DEFAULT_LOCALE):
    """Read known native formats. No generic binary/string scraping."""
    base = canonical_name(path.name)
    target_key = target_field(locale)
    entries = []
    if path.suffix == ".xliff":
        tree = parse(path)
        if tree.getroot().get("version") != "2.0":
            raise ValueError("Unsupported XLIFF version: " + relative)
        for fi, file in enumerate(tree.findall("x:file", N)):
            file_id = file.get("id") or file.get("original") or f"file-{fi}"
            for unit in file.findall(".//x:unit", N):
                unit_id = unit.get("id")
                if not unit_id:
                    raise ValueError("Unit missing native ID: " + relative)
                notes = ["".join(n.itertext()) for n in unit.findall("x:notes/x:note", N)]
                for si, segment in enumerate(unit.findall("x:segment", N)):
                    source = segment.find("x:source", N)
                    if source is None:
                        raise ValueError("Segment missing source: " + relative)
                    text = inner(source)
                    entries.append({
                        "id": f"{base}::{file_id}::{unit_id}::segment-{si + 1}",
                        "file_index": fi, "file_id": file_id, "unit_id": unit_id,
                        "segment_index": si,
                        "source": text, target_key: "",
                        "source_format": "xml_fragment" if len(source) else "text",
                        "context": base.removesuffix(".xliff") + " / " + unit_id,
                        "notes": notes,
                        "requires_translation": bool(text),
                        "translator_note": "",
                    })
        kind = "xliff2"
        folder = category(base)
    elif path.suffix == ".csv":
        rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig")), delimiter=";"))
        header = rows[0]
        expected = ["SPECIES_ID", "ABBR", "GENDER", "ONE", "FEW", "MANY", "OTHER", "CLASSIFIER", "DEFINITE_ART"]
        if header != expected:
            raise ValueError("Unexpected species CSV header")
        for ri, row in enumerate(rows[1:], start=1):
            if not row or not row[0]:
                continue
            if len(row) != len(header):
                raise ValueError("Invalid CSV row width")
            values = dict(zip(header, row))
            for field in FIELDS:
                text = values[field]
                entries.append({
                    "id": f"{base}::{values['SPECIES_ID']}::{field}",
                    "row_index": ri, "species_id": values["SPECIES_ID"], "field": field,
                    "source": text, target_key: "", "source_format": "text",
                    "context": f"{values['SPECIES_ID']} / {field}; ONE={values['ONE']}; GENDER={values['GENDER']}",
                    "notes": ["只翻譯顯示文字；SPECIES_ID、欄名、GENDER 代碼保持不變。原文空白欄可保留空白。"],
                    "requires_translation": bool(text), "translator_note": "",
                })
        kind, folder = "species_semicolon_csv", "05_species"
    else:
        raise ValueError("Unsupported input suffix")
    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate stable IDs: " + relative)
    return {
        "format": "xwvm-translation-workspace-v1", "native_format": kind,
        "source_file": relative, "target_locale": locale,
        "instructions": f"只編輯 {target_key} 與 translator_note。空白 target 匯出時保留英文；這份 JSON 不是遊戲原生格式。",
        "entries": entries,
    }, folder + "/" + base + ".json"


def split_top(text, delimiter):
    parts, start, depth = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == delimiter and depth == 0:
            parts.append(text[start:i]); start = i + 1
    parts.append(text[start:])
    return parts


def smart_signature(text):
    """Conservative syntax check, not an implementation of Unity SmartFormat."""
    escaped = re.findall(r"\\+[{}nrt]", text)
    text = re.sub(r"\\+[{}]", "", text)
    result, stack = [], []
    for i, ch in enumerate(text):
        if ch == "{":
            stack.append(i)
        elif ch == "}":
            if not stack:
                raise ValueError("unmatched closing brace")
            start = stack.pop()
            body = text[start + 1:i]
            parts = split_top(body, ":")
            if len(parts) == 1:
                # Bare "{}" (the current value) may appear in more plural branches than the source:
                # Unity's SmartFormat always picks the first plural branch for zh, so every branch
                # must be the general form (e.g. "{} 款遊戲|{} 款遊戲").
                if parts[0] == "":
                    continue
                result.append((parts[0], "plain", 0))
            elif len(parts) >= 3 and re.fullmatch(r"[A-Za-z_]\w*(\(.*\))?", parts[1], re.S):
                result.append((parts[0], parts[1], len(split_top(":".join(parts[2:]), "|"))))
            elif len(parts) >= 3:
                # Not a formatter name (e.g. "{game:Achievement Progress: {game}|...}"): SmartFormat
                # treats everything after the first ":" as the format text, colons included.
                result.append((parts[0], "default", len(split_top(":".join(parts[1:]), "|"))))
            elif re.fullmatch(r"[A-Za-z][0-9]*", parts[1]):
                result.append((parts[0], "format:" + parts[1], 0))
            else:
                result.append((parts[0], "default", len(split_top(parts[1], "|"))))
    if stack:
        raise ValueError("unclosed brace")
    return Counter(result), Counter(escaped)


def markup_signature(text):
    # XWVM's rich-text tokens and in-flight highlighting are significant.
    tags = Counter(re.findall(r"</?[A-Za-z][^>]*>", text))
    marks = Counter({s: text.count(s) for s in ["[[", "]]", "((", "))", "(*", "*)"]})
    return tags, marks


def expected_signature(source, locale):
    """Source SmartString signature with plural branch counts adjusted to the target language's rules."""
    smart, escaped = smart_signature(source)
    forms = PLURAL_FORMS.get(language_of(locale))
    if forms:
        smart = Counter({(name, fmt, forms if fmt.startswith("plural") else count): n
                         for (name, fmt, count), n in smart.items()})
    return smart, escaped


def plural_branches(text):
    """Branch texts of each {x:plural:...} in text."""
    result = []
    for m in re.finditer(r"\{[^{}:]*:plural(?:\([^)]*\))?:", text):
        depth, start = 1, m.end()
        for i in range(start, len(text)):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            if depth == 0:
                result.append(split_top(text[start:i], "|"))
                break
    return result


def check_translation(source, target, source_format="text", locale=DEFAULT_LOCALE):
    errors = []
    if not target:
        return errors
    if any(ord(c) < 32 and c not in "\n\r\t" for c in target):
        errors.append("XML 不允許的控制字元")
    try:
        if expected_signature(source, locale) != smart_signature(target):
            forms = PLURAL_FORMS.get(language_of(locale))
            errors.append("SmartString 變數、格式器、選項或分支數不一致"
                          + (f"（{locale} 的複數需要 {forms} 個分支）" if forms and ":plural" in source else ""))
    except ValueError as e:
        errors.append("大括號結構錯誤: " + str(e))
    if markup_signature(source) != markup_signature(target):
        errors.append("富文字標籤或 [[ ]] / (( )) / (* *) 標記不一致")
    if source_format == "xml_fragment":
        try:
            ET.fromstring(f'<target xmlns="{NS}">' + target + "</target>")
        except ET.ParseError as e:
            errors.append("行內 XML 格式錯誤: " + str(e))
    return errors


def init_workspace(source, out, locale=DEFAULT_LOCALE):
    source, out = source.resolve(), out.resolve()
    if out.exists():
        raise ValueError("輸出目錄已存在；拒絕覆寫翻譯工作。請另選新的 --out。")
    files = [p for p in sorted((source / "XLIFF/es").glob("*.xliff")) if ".tf." not in p.name]
    files += [source / "CSV/XWVM.xwing.Species_en.csv"]
    if len(files) != 32:
        raise ValueError("來源版本/檔案數已改變；需人工重新盤點後調整抽取範圍。預期 31 XLIFF + 1 CSV。")
    plans = []
    for p in files:
        rel = p.relative_to(source).as_posix()
        doc, translation = make_document(p, rel, locale)
        plans.append((p, rel, doc, translation))
    out.mkdir(parents=True)
    manifest = {"version": 1, "target_locale": locale, "source_install": str(source), "app_version": "1.0.20260923.2004",
                "scope": "Installed XWVM Spanish-template English sources, excluding TIE Fighter; English X-Wing species metadata.",
                "native_import_verified": False, "files": []}
    for p, rel, doc, translation in plans:
        dest = out / "reference" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        write_json(out / "translate" / translation, doc)
        manifest["files"].append({"source": rel, "bytes": p.stat().st_size, "sha256": sha(p),
                                  "translation": translation, "entries": len(doc["entries"]),
                                  "nonempty_sources": sum(e["requires_translation"] for e in doc["entries"])})
    shutil.copyfile(source / "LICENSE", out / "LICENSE-XWVM-localization.txt")
    write_json(out / "manifest.json", manifest)
    return manifest


def workspace_locale(manifest):
    # Workspaces created before the locale parameter existed are zh-TW.
    return manifest.get("target_locale", DEFAULT_LOCALE)


def validate(root, complete=False):
    manifest = read_json(root / "manifest.json")
    locale = workspace_locale(manifest)
    field = target_field(locale)
    single_form = language_of(locale) in SINGLE_FORM_LANGUAGES
    errors, warnings = [], []
    total = required = translated = translated_required = 0
    chars = set()
    known = {f["translation"] for f in manifest["files"]}
    found = {p.relative_to(root / "translate").as_posix() for p in (root / "translate").rglob("*.json")}
    if known != found:
        errors.append("翻譯檔案集合改變: missing=" + str(sorted(known - found)) + "; extra=" + str(sorted(found - known)))
    for item in manifest["files"]:
        rel = item["source"]
        reference = root / "reference" / rel
        try:
            if sha(reference) != item["sha256"]:
                errors.append("參考檔 SHA-256 不符: " + rel)
                continue
            expected, _ = make_document(reference, rel, locale)
            doc = read_json(root / "translate" / item["translation"])
            if {k:v for k,v in doc.items() if k != "entries"} != {k:v for k,v in expected.items() if k != "entries"}:
                errors.append("檔案中繼資料遭更動: " + rel)
            entries = doc["entries"]
            index = {e["id"]:e for e in entries}
            if len(index) != len(entries):
                errors.append("重複 ID: " + rel)
            if set(index) != {e["id"] for e in expected["entries"]}:
                errors.append("ID 集合不符: " + rel)
                continue
            for baseline in expected["entries"]:
                e = index[baseline["id"]]
                immutable = lambda d: {k:v for k,v in d.items() if k not in (field, "translator_note")}
                if immutable(e) != immutable(baseline):
                    errors.append("原文/ID/情境欄位遭更動: " + e["id"])
                target = e.get(field)
                if not isinstance(target, str) or not isinstance(e.get("translator_note"), str):
                    errors.append("翻譯與筆記必須是字串: " + e["id"])
                    continue
                total += 1; required += baseline["requires_translation"]
                translated += bool(target); translated_required += bool(target) and baseline["requires_translation"]
                chars.update(target)
                if complete and baseline["requires_translation"] and not target:
                    errors.append("未翻譯: " + e["id"])
                for msg in check_translation(baseline["source"], target, baseline["source_format"], locale):
                    errors.append(msg + ": " + e["id"])
                if single_form and target and any(len(set(b)) > 1 for b in plural_branches(target)):
                    warnings.append("此語言永遠只取第一個複數分支，各分支應寫成相同的通用形: " + e["id"])
                if target and target == baseline["source"]:
                    warnings.append("譯文仍與原文相同: " + e["id"])
                if target and baseline["source"].count("\n") != target.count("\n"):
                    warnings.append("換行數改變，需檢查版面: " + e["id"])
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as e:
            errors.append(rel + ": " + str(e))
    return {"ok": not errors, "locale": locale, "entries": total, "required_nonempty_sources": required,
            "translated_entries": translated, "translated_required": translated_required,
            "untranslated_required": required - translated_required,
            "errors": errors, "warnings": warnings,
            "translated_unicode_codepoints": len(chars),
            "game_runtime_tested": False, "font_support_verified": False}


def assign_target(segment, entry, field=target_field(DEFAULT_LOCALE)):
    src = segment.find("x:source", N)
    target = segment.find("x:target", N)
    if target is not None:
        segment.remove(target)
    translation = entry[field]
    if not translation:
        target = copy.deepcopy(src)
        target.tag = "{" + NS + "}target"
    elif entry["source_format"] == "xml_fragment":
        target = ET.fromstring(f'<target xmlns="{NS}">' + translation + "</target>")
    else:
        target = ET.Element("{" + NS + "}target")
        target.text = translation
    segment.insert(list(segment).index(src) + 1, target)
    segment.set("state", "translated" if translation else "initial")


def build(root, label):
    result = validate(root)
    if not result["ok"]:
        raise ValueError("驗證失敗，未產生匯出。\n" + "\n".join(result["errors"][:10]))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", label):
        raise ValueError("匯出名稱只接受英數、底線、連字號，不能指定外部路徑。")
    export_base = root / "exports"
    if export_base.is_symlink():
        raise ValueError("拒絕寫入符號連結 exports 目錄。")
    out = export_base / label
    if out.exists():
        raise ValueError("匯出目錄已存在；請使用新名稱，避免覆寫。")
    out.mkdir(parents=True)
    manifest = read_json(root / "manifest.json")
    locale = workspace_locale(manifest)
    field = target_field(locale)
    output_records = []
    allchars = set()
    for item in manifest["files"]:
        ref = root / "reference" / item["source"]
        doc = read_json(root / "translate" / item["translation"])
        entries = doc["entries"]
        if doc["native_format"] == "xliff2":
            tree = parse(ref)
            rt = tree.getroot()
            rt.set("trgLang", locale)
            files = rt.findall("x:file", N)
            for file in files:
                if "trgLang" in file.attrib:
                    file.set("trgLang", locale)
            # Group by original file index and unit ID; one native segment per record.
            unit_maps = [{u.get("id"):u for u in f.findall(".//x:unit", N)} for f in files]
            for entry in entries:
                unit = unit_maps[entry["file_index"]][entry["unit_id"]]
                assign_target(unit.findall("x:segment", N)[entry["segment_index"]], entry, field)
                allchars.update(entry[field] or entry["source"])
            dest = out / "Localization/XLIFF" / locale / ref.name.replace("_es.", f"_{locale}.")
            dest.parent.mkdir(parents=True, exist_ok=True)
            tree.write(dest, encoding="utf-8", xml_declaration=True)
            parse(dest)  # Verify the generated XML is readable.
        else:
            rows = list(csv.reader(io.StringIO(ref.read_text(encoding="utf-8-sig")), delimiter=";"))
            for entry in entries:
                value = entry[field] or entry["source"]
                rows[entry["row_index"]][rows[0].index(entry["field"])] = value
                allchars.update(value)
            dest = out / "Localization/CSV" / ref.name.replace("_en.", f"_{locale}.")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", encoding="utf-8", newline="") as f:
                csv.writer(f, delimiter=";", lineterminator="\n").writerows(rows)
        output_records.append({"path": dest.relative_to(out).as_posix(), "bytes": dest.stat().st_size, "sha256": sha(dest)})
    write_json(out / "build-report.json", {"validation": result, "files": output_records,
               "meaning": f"本機 {locale} XLIFF/CSV 匯出候選，尚未安裝或通過遊戲載入、字型與 SmartFormat 執行驗證。未翻譯欄位使用英文原文。"})
    (out / "font-characters.txt").write_text("".join(sorted(c for c in allchars if not c.isspace())) + "\n", encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["extract", "validate", "build", "verify-sources"])
    parser.add_argument("--root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--name", default="candidate-001")
    parser.add_argument("--locale", default=DEFAULT_LOCALE,
                        help="extract 時的目標語系（xx 或 xx-YY，例如 ja、ko、zh-TW）；validate/build 讀取工作區 manifest 記錄的語系")
    args = parser.parse_args()
    try:
        if args.command == "extract":
            manifest = init_workspace(args.source, args.out, args.locale)
            print(json.dumps({"path": str(args.out), "locale": args.locale, "files": len(manifest["files"]), "entries": sum(f["entries"] for f in manifest["files"])}, ensure_ascii=False))
        elif args.command == "validate":
            report = validate(args.root, args.complete)
            write_json(args.root / "reports/validation.json", report)
            print(json.dumps({k:v for k,v in report.items() if k not in ["errors", "warnings"]}, ensure_ascii=False))
            if report["errors"]: print("\n".join(report["errors"][:15]))
            return 0 if report["ok"] else 1
        elif args.command == "build":
            print(build(args.root, args.name))
        else:
            manifest = read_json(args.root / "manifest.json")
            mismatches = [f["source"] for f in manifest["files"] if sha(args.source / f["source"]) != f["sha256"]]
            print(json.dumps({"unchanged": not mismatches, "files_checked": len(manifest["files"]), "mismatches": mismatches}))
            return 1 if mismatches else 0
    except (OSError, ValueError, KeyError, ET.ParseError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
