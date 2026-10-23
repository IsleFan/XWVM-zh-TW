"""Tests the real installed-format snapshot; never starts the game."""
import copy
import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

import localization_tool as tool


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="xwvm-localization-test-")
        cls.root = Path(cls.temp.name) / "workspace"
        shutil.copytree(tool.DEFAULT_OUT / "reference", cls.root / "reference")
        shutil.copyfile(tool.DEFAULT_OUT / "manifest.json", cls.root / "manifest.json")
        cls.manifest = tool.read_json(cls.root / "manifest.json")
        # Regenerate the blank test fixtures from immutable references, so tests
        # do not depend on or touch the user's translation progress.
        for item in cls.manifest["files"]:
            doc, relative = tool.make_document(cls.root / "reference" / item["source"], item["source"])
            tool.write_json(cls.root / "translate" / relative, doc)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def mutate_and_validate(self, mutate):
        item = self.manifest["files"][0]
        path = self.root / "translate" / item["translation"]
        original = path.read_bytes()
        try:
            doc = tool.read_json(path)
            mutate(doc)
            tool.write_json(path, doc)
            return tool.validate(self.root)
        finally:
            path.write_bytes(original)

    def test_baseline_counts_and_no_translations(self):
        result = tool.validate(self.root)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["entries"], 9391)
        self.assertEqual(result["required_nonempty_sources"], 8940)
        self.assertEqual(result["translated_entries"], 0)

    def test_complete_check_refuses_unfinished_pack(self):
        result = tool.validate(self.root, complete=True)
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["errors"]), 8940)

    def test_modified_source_is_rejected(self):
        result = self.mutate_and_validate(lambda d: d["entries"][0].update(source="edited"))
        self.assertFalse(result["ok"])

    def test_duplicate_and_missing_id_are_rejected(self):
        for mutation in [lambda d: d["entries"].append(copy.deepcopy(d["entries"][0])),
                         lambda d: d["entries"].pop()]:
            with self.subTest(mutation=str(mutation)):
                self.assertFalse(self.mutate_and_validate(mutation)["ok"])

    def test_broken_json_is_rejected(self):
        path = self.root / "translate" / self.manifest["files"][0]["translation"]
        data = path.read_bytes()
        try:
            path.write_text('{"bad":', encoding="utf-8")
            self.assertFalse(tool.validate(self.root)["ok"])
        finally:
            path.write_bytes(data)

    def test_unicode_translation_and_progress(self):
        result = self.mutate_and_validate(lambda d: d["entries"][0].update(target_zh_TW="未知編隊"))
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["translated_required"], 1)

    def test_native_roundtrip_all_sources_and_ids(self):
        out = tool.build(self.root, "roundtrip")
        count = 0
        for item in self.manifest["files"]:
            ref = self.root / "reference" / item["source"]
            if ref.suffix != ".xliff":
                generated = out / "Localization/CSV" / ref.name.replace("_en.", "_zh-TW.")
                reader = lambda p: list(csv.reader(io.StringIO(p.read_text(encoding="utf-8-sig")), delimiter=";"))
                self.assertEqual(reader(ref), reader(generated))
                continue
            generated = out / "Localization/XLIFF/zh-TW" / ref.name.replace("_es.", "_zh-TW.")
            original, new = tool.parse(ref), tool.parse(generated)
            self.assertEqual(new.getroot().get("trgLang"), "zh-TW")
            oldunits = original.findall(".//x:unit", tool.N)
            newunits = new.findall(".//x:unit", tool.N)
            self.assertEqual([u.get("id") for u in oldunits], [u.get("id") for u in newunits])
            for a, b in zip(oldunits, newunits):
                for sa, sb in zip(a.findall("x:segment", tool.N), b.findall("x:segment", tool.N)):
                    self.assertEqual(tool.inner(sa.find("x:source", tool.N)), tool.inner(sb.find("x:source", tool.N)))
                    self.assertEqual(tool.inner(sb.find("x:source", tool.N)), tool.inner(sb.find("x:target", tool.N)))
                    count += 1
        self.assertEqual(count, 8677)

    def test_translated_xml_fragment_and_csv_roundtrip(self):
        originals = {}
        try:
            for item in self.manifest["files"]:
                path = self.root / "translate" / item["translation"]
                doc = tool.read_json(path)
                changed = False
                if "Concourse" in item["source"]:
                    entry = next(e for e in doc["entries"] if e["source_format"] == "xml_fragment")
                    entry["target_zh_TW"] = entry["source"].replace("Clone Pilot", "複製飛行員")
                    changed = True
                elif item["source"].endswith("Species_en.csv"):
                    entry = next(e for e in doc["entries"] if e["species_id"] == "XWing" and e["field"] == "ONE")
                    entry["target_zh_TW"] = 'X 翼;測試 "引號"\n換行'
                    changed = True
                if changed:
                    originals[path] = path.read_bytes()
                    tool.write_json(path, doc)
            out = tool.build(self.root, "unicode-roundtrip")
            xlf = tool.parse(out / "Localization/XLIFF/zh-TW/XWVM.xwing.Concourse_zh-TW.xliff")
            unit = next(u for u in xlf.findall(".//x:unit", tool.N) if u.get("id") == "Registration.Pilot.ClonePilot.CloneText")
            self.assertIn("複製飛行員", tool.inner(unit.find("x:segment/x:target", tool.N)))
            self.assertIsNotNone(unit.find("x:segment/x:target/x:b", tool.N))
            with (out / "Localization/CSV/XWVM.xwing.Species_zh-TW.csv").open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f, delimiter=";"))
            row = next(r for r in rows if r["SPECIES_ID"] == "XWing")
            self.assertEqual(row["ONE"], 'X 翼;測試 "引號"\n換行')
        finally:
            for path, content in originals.items():
                path.write_bytes(content)

    def test_no_overwrite_or_path_escape(self):
        tool.build(self.root, "existing")
        for name in ["existing", "../../game", "/Applications/XWVM", "a/b"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                tool.build(self.root, name)
        with self.assertRaises(ValueError):
            tool.init_workspace(self.root / "reference", self.root)

    def test_source_hash_tampering_is_detected(self):
        ref = self.root / "reference" / self.manifest["files"][0]["source"]
        original = ref.read_bytes()
        try:
            ref.write_bytes(original + b"\n")
            self.assertFalse(tool.validate(self.root)["ok"])
        finally:
            ref.write_bytes(original)


class OtherLocaleTests(unittest.TestCase):
    """A workspace for another language: field names, export paths and plural rules follow the locale."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="xwvm-localization-locale-test-")
        source = Path(cls.temp.name) / "install"
        shutil.copytree(tool.DEFAULT_OUT / "reference", source)
        shutil.copyfile(tool.DEFAULT_OUT / "LICENSE-XWVM-localization.txt", source / "LICENSE")
        cls.root = Path(cls.temp.name) / "ja-workspace"
        cls.manifest = tool.init_workspace(source, cls.root, "ja")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def edit_entry(self, predicate, value):
        """Sets target_ja on the first matching entry; returns a function restoring the file."""
        for item in self.manifest["files"]:
            path = self.root / "translate" / item["translation"]
            doc = tool.read_json(path)
            entry = next((e for e in doc["entries"] if predicate(e)), None)
            if entry:
                original = path.read_bytes()
                entry["target_ja"] = value
                tool.write_json(path, doc)
                return lambda: path.write_bytes(original)
        self.fail("no matching entry")

    def test_workspace_uses_locale_field(self):
        self.assertEqual(self.manifest["target_locale"], "ja")
        doc = tool.read_json(self.root / "translate" / self.manifest["files"][0]["translation"])
        self.assertEqual(doc["target_locale"], "ja")
        self.assertIn("target_ja", doc["entries"][0])
        self.assertNotIn("target_zh_TW", doc["entries"][0])
        result = tool.validate(self.root)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["locale"], "ja")

    def test_export_paths_and_language_attributes(self):
        restore = self.edit_entry(lambda e: e["id"].startswith("XWVM.UI.GameLibrary.xliff::") and e["unit_id"] == "MainMenu.Label.StartGame",
                                  "ゲーム開始")
        try:
            out = tool.build(self.root, "ja-export")
        finally:
            restore()
        xlf = tool.parse(out / "Localization/XLIFF/ja/XWVM.UI.GameLibrary_ja.xliff")
        self.assertEqual(xlf.getroot().get("trgLang"), "ja")
        unit = next(u for u in xlf.findall(".//x:unit", tool.N) if u.get("id") == "MainMenu.Label.StartGame")
        self.assertEqual(unit.find("x:segment/x:target", tool.N).text, "ゲーム開始")
        self.assertTrue((out / "Localization/CSV/XWVM.xwing.Species_ja.csv").is_file())
        self.assertFalse((out / "Localization/XLIFF/zh-TW").exists())

    def test_single_form_language_warns_on_different_plural_branches(self):
        is_count = lambda e: e["unit_id"] == "Library.Value.LibraryCount"
        restore = self.edit_entry(is_count, "{gameCount:plural:1 本|{} 本} インストール済み")
        try:
            result = tool.validate(self.root)
        finally:
            restore()
        self.assertTrue(result["ok"], result["errors"])
        self.assertTrue(any("LibraryCount" in w and "第一個複數分支" in w for w in result["warnings"]))

    def test_invalid_locale_code_is_rejected(self):
        for code in ["zh_TW", "zh-Hant", "jpn", "../x", ""]:
            with self.subTest(code=code), self.assertRaises(ValueError):
                tool.target_field(code)


class SyntaxTests(unittest.TestCase):
    def test_plural_branch_count_follows_target_language(self):
        source = "{count:plural:1 ship|{} ships}"
        # Chinese/Japanese use the first branch only; the general form may add "{}" to every branch.
        self.assertEqual(tool.check_translation(source, "{count:plural:{} 艘|{} 艘}", locale="zh-TW"), [])
        # Russian SmartFormat rule returns branch 0..2, so three branches are required.
        self.assertEqual(tool.check_translation(source, "{count:plural:{} корабль|{} корабля|{} кораблей}", locale="ru"), [])
        self.assertTrue(tool.check_translation(source, "{count:plural:{} корабль|{} кораблей}", locale="ru"))
        self.assertEqual(tool.check_translation(source, "{count:plural:{} statek|{} statki|{} statków|{} statku}", locale="pl"), [])
        self.assertTrue(tool.check_translation(source, "{count:plural:{} navire|{} navires|{} x}", locale="fr"))

    def test_placeholders_reorder_and_missing(self):
        self.assertEqual(tool.check_translation("Page {pIndex} / {pCount}", "共 {pCount} 頁，第 {pIndex} 頁"), [])
        self.assertTrue(tool.check_translation("Page {pIndex} / {pCount}", "第 {pIndex} 頁"))

    def test_nested_smartstrings_and_branch_keys(self):
        source = "{target:choose(null):target cleared|set to target [[{}]]}"
        self.assertEqual(tool.check_translation(source, "{target:choose(null):目標已清除|目標設為 [[{}]]}"), [])
        self.assertTrue(tool.check_translation(source, "{target:choose(空):目標已清除|目標設為 [[{}]]}"))
        self.assertTrue(tool.check_translation(source, "{target:choose(null):目標已清除}"))

    def test_braces_tags_markers_escapes(self):
        for source, target in [("{name}", "{name"), ("<b>Title</b>", "<b>標題"),
                               ("[[Ship]]", "飛船"), (r"A\nB", "甲\n乙")]:
            with self.subTest(source=source):
                self.assertTrue(tool.check_translation(source, target))

    def test_inline_xml_and_ampersand_roundtrip(self):
        self.assertEqual(tool.check_translation("<b>Clone Pilot</b>", "<b>複製飛行員</b>", "xml_fragment"), [])
        self.assertTrue(tool.check_translation("<b>Clone Pilot</b>", "<b>複製 & 飛行員</b>", "xml_fragment"))
        segment = ET.fromstring(f'<segment xmlns="{tool.NS}"><source>Alpha</source><target>Beta</target></segment>')
        tool.assign_target(segment, {"target_zh_TW": '測試 & <文字> "引號"', "source_format": "text"})
        reread = ET.fromstring(ET.tostring(segment))
        self.assertEqual(reread.find("x:target", tool.N).text, '測試 & <文字> "引號"')


if __name__ == "__main__":
    unittest.main(verbosity=2)
