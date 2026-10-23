#!/usr/bin/env python3
"""Build the end-user release zips (macOS and Windows) into release/dist/.

    python3 release/build_release.py v0.9.0-beta [language pack export name, default zh-TW-v1]

Each zip holds only prebuilt files: the plugin DLL, the UI translation tables, the language pack
and double-click installer scripts. Nothing has to be compiled or installed by the user.
"""
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "font-plugin"
RELEASE = REPO / "release"


class ZipBuilder:
    def __init__(self, path, top):
        self.zip = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9)
        self.top = top

    def add_bytes(self, name, data, executable=False):
        info = zipfile.ZipInfo(f"{self.top}/{name}", date_time=(2026, 10, 23, 0, 0, 0))
        info.create_system = 3  # Unix, so macOS Archive Utility keeps the permission bits
        info.external_attr = (0o100755 if executable else 0o100644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        # zipfile marks non-ASCII names as UTF-8 (flag 0x800), so Chinese file names survive on Windows.
        self.zip.writestr(info, data)

    def add_file(self, name, path, executable=False):
        self.add_bytes(name, path.read_bytes(), executable)

    def add_tree(self, prefix, folder):
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.name != ".DS_Store":
                self.add_file(f"{prefix}/{path.relative_to(folder).as_posix()}", path)

    def close(self):
        self.zip.close()


def templated(path, version, windows=False):
    text = path.read_text(encoding="utf-8-sig").replace("{{VERSION}}", version)
    if windows:
        # Notepad and cmd expect CRLF; the BOM makes Notepad pick UTF-8 for Chinese text.
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if path.suffix == ".txt" else b"") + text.encode("utf-8")
    return text.encode("utf-8")


def add_common(z, pack):
    z.add_file("files/XwvmChineseFont.dll", PLUGIN / "XwvmChineseFont.dll")
    for table in sorted(PLUGIN.glob("XwvmChineseFont-*.json")):
        z.add_file(f"files/{table.name}", table)
    z.add_tree(f"files/{pack.name}/Localization", pack / "Localization")


def build(version, pack_name):
    pack = REPO / "translation" / "exports" / pack_name
    if not (pack / "Localization").is_dir():
        sys.exit(f"Language pack not found: {pack}")
    dist = RELEASE / "dist"
    dist.mkdir(exist_ok=True)
    outputs = []

    mac = dist / f"XWVM-zh-TW-{version}-macOS.zip"
    z = ZipBuilder(mac, "XWVM 繁體中文化 (macOS)")
    for script in ["安裝中文化.command", "移除中文化.command"]:
        z.add_bytes(script, templated(RELEASE / "macos" / script, version), executable=True)
    z.add_bytes("使用說明.txt", templated(RELEASE / "macos" / "使用說明.txt", version))
    add_common(z, pack)
    z.add_file("files/register_plugin.js", PLUGIN / "register_plugin.js")
    z.add_file("files/install_mac.sh", PLUGIN / "install_mac.sh", executable=True)
    z.add_file("files/install_language_mac.sh", REPO / "translation" / "install_language_mac.sh", executable=True)
    z.close()
    outputs.append(mac)

    win = dist / f"XWVM-zh-TW-{version}-Windows.zip"
    z = ZipBuilder(win, "XWVM 繁體中文化 (Windows)")
    for name in ["安裝中文化.bat", "移除中文化.bat", "使用說明.txt"]:
        z.add_bytes(name, templated(RELEASE / "windows" / name, version, windows=True))
    add_common(z, pack)
    z.add_file("files/install_windows.ps1", PLUGIN / "install_windows.ps1")  # kept with its UTF-8 BOM
    z.close()
    outputs.append(win)

    for path in outputs:
        print(f"{path}  ({path.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "zh-TW-v1")
