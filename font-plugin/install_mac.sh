#!/bin/sh
# Make a CJK-font-enabled copy of XWVM next to the original app (macOS, no Python needed).
# The original xwvm.app is not touched; the copy is an APFS clone, so it uses almost no disk space.
# Re-run after every XWVM update (it rebuilds the copy from the updated original).
#
#   ./install_mac.sh [path/to/xwvm.app] [path/to/copy.app]
#   ./install_mac.sh --uninstall [path/to/copy.app]
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "$1" = "--uninstall" ]; then
    DST_APP="${2:-/Applications/XWVM/xwvm-zhTW.app}"
    rm -rf "$DST_APP"
    echo "Removed $DST_APP"
    exit 0
fi

SRC_APP="${1:-/Applications/XWVM/xwvm.app}"
DST_APP="${2:-$(dirname "$SRC_APP")/xwvm-zhTW.app}"

[ -d "$SRC_APP/Contents/Resources/Data/Managed" ] || { echo "XWVM not found: $SRC_APP" >&2; exit 1; }

rm -rf "$DST_APP"
cp -cR "$SRC_APP" "$DST_APP" 2>/dev/null || cp -R "$SRC_APP" "$DST_APP"

DATA="$DST_APP/Contents/Resources/Data"
cp "$HERE/XwvmChineseFont.dll" "$HERE"/XwvmChineseFont-*.json "$DATA/Managed/"
[ -f "$HERE/XwvmChineseFont.ini" ] && cp "$HERE/XwvmChineseFont.ini" "$DATA/Managed/"
[ -d "$HERE/XwvmChineseFont-fonts" ] && cp -R "$HERE/XwvmChineseFont-fonts" "$DATA/Managed/"
osascript -l JavaScript "$HERE/register_plugin.js" "$DATA"

# The bundle contents changed, so re-apply the same ad-hoc signature the original uses.
codesign --force --deep --sign - "$DST_APP"
echo "Done. Start XWVM with: open \"$DST_APP\""
