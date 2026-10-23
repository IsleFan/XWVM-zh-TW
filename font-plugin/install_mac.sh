#!/bin/sh
# Make a Chinese-font-enabled copy of XWVM next to the original app.
# The original xwvm.app is not touched; the copy is an APFS clone, so it uses almost no disk space.
# Re-run after every XWVM update (it rebuilds the copy from the updated original).
set -e

SRC_APP="${1:-/Applications/XWVM/xwvm.app}"
DST_APP="${2:-$(dirname "$SRC_APP")/xwvm-zhTW.app}"
HERE="$(cd "$(dirname "$0")" && pwd)"

[ -d "$SRC_APP" ] || { echo "XWVM not found: $SRC_APP" >&2; exit 1; }

rm -rf "$DST_APP"
cp -cR "$SRC_APP" "$DST_APP" 2>/dev/null || cp -R "$SRC_APP" "$DST_APP"

python3 "$HERE/patch_xwvm.py" "$DST_APP/Contents/Resources/Data" "$HERE/XwvmChineseFont.dll"
[ -f "$HERE/XwvmChineseFont.ini" ] && cp "$HERE/XwvmChineseFont.ini" "$DST_APP/Contents/Resources/Data/Managed/"
[ -d "$HERE/XwvmChineseFont-fonts" ] && cp -R "$HERE/XwvmChineseFont-fonts" "$DST_APP/Contents/Resources/Data/Managed/"

# The bundle contents changed, so re-apply the same ad-hoc signature the original uses.
codesign --force --deep --sign - "$DST_APP"
echo "Done. Start XWVM with: open \"$DST_APP\""
