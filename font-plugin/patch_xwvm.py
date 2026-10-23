#!/usr/bin/env python3
"""Install XwvmChineseFont.dll into an XWVM Unity data folder.

Copies the DLL into <data>/Managed and registers it so Unity loads it at startup:
  - ScriptingAssemblies.json : adds the assembly (type 16 = user assembly)
  - RuntimeInitializeOnLoads.json : calls ChineseFontLoader.Init before the first scene

<data> is the folder that contains Managed/ and ScriptingAssemblies.json:
  macOS   : XWVM.app/Contents/Resources/Data
  Windows : <install dir>/XWVM_Data   (folder name = exe name + "_Data")

Originals are kept as *.orig the first time. Running it again is safe.
Usage: python3 patch_xwvm.py <data folder> [path/to/XwvmChineseFont.dll] [--uninstall]
"""
import json
import shutil
import sys
from pathlib import Path

ASSEMBLY = "XwvmChineseFont"
INIT_ENTRY = {
    "assemblyName": ASSEMBLY,
    "nameSpace": "XwvmChineseFont",
    "className": "FallbackFontLoader",
    "methodName": "Init",
    "loadTypes": 1,  # RuntimeInitializeLoadType.BeforeSceneLoad
    "isUnityClass": False,
}


def load_json(path):
    backup = path.with_name(path.name + ".orig")
    if not backup.exists():
        shutil.copy2(path, backup)
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))


def main(argv):
    uninstall = "--uninstall" in argv
    args = [a for a in argv if a != "--uninstall"]
    if not args:
        sys.exit(__doc__)
    data = Path(args[0])
    dll = Path(args[1]) if len(args) > 1 else Path(__file__).with_name(ASSEMBLY + ".dll")

    assemblies_path = data / "ScriptingAssemblies.json"
    init_path = data / "RuntimeInitializeOnLoads.json"
    managed = data / "Managed"
    for p in (assemblies_path, init_path, managed):
        if not p.exists():
            sys.exit(f"Not an XWVM data folder (missing {p})")

    assemblies = load_json(assemblies_path)
    inits = load_json(init_path)
    name = ASSEMBLY + ".dll"

    # Remove any previous registration first so the result is identical on every run.
    keep = [i for i, n in enumerate(assemblies["names"]) if n != name]
    assemblies["names"] = [assemblies["names"][i] for i in keep]
    assemblies["types"] = [assemblies["types"][i] for i in keep]
    inits["root"] = [e for e in inits["root"] if e.get("assemblyName") != ASSEMBLY]

    # Per-locale UI translations (control-mapping window etc.), XwvmChineseFont-<locale>.json.
    ui_pattern = ASSEMBLY + "-*.json"
    for old in managed.glob(ui_pattern):
        old.unlink()
    if uninstall:
        (managed / name).unlink(missing_ok=True)
    else:
        if not dll.is_file():
            sys.exit(f"DLL not found: {dll}")
        shutil.copy2(dll, managed / name)
        for table in dll.parent.glob(ui_pattern):
            shutil.copy2(table, managed / table.name)
        assemblies["names"].append(name)
        assemblies["types"].append(16)
        inits["root"].append(INIT_ENTRY)

    save_json(assemblies_path, assemblies)
    save_json(init_path, inits)
    print(("Removed from " if uninstall else "Installed into ") + str(data))


if __name__ == "__main__":
    main(sys.argv[1:])
