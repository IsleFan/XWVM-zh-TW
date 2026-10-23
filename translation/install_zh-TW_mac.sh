#!/bin/sh
# Install a zh-TW language pack built by `tools/localization_tool.py build --name <name>` into XWVM (macOS).
# XWVM's StreamingAssets folder is owned by root, so sudo asks for your password.
#
#   ./install_zh-TW_mac.sh <name>        e.g. ./install_zh-TW_mac.sh zh-TW-v1
#   ./install_zh-TW_mac.sh --uninstall   removes the zh-TW files again
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
LOC="/Library/Application Support/XWVM Team/XWVM/StreamingAssets/Localization"

if [ "$1" = "--uninstall" ]; then
    sudo rm -rf "$LOC/XLIFF/zh-TW"
    sudo rm -f "$LOC/CSV/"*_zh-TW.csv
    echo "zh-TW removed."
    exit 0
fi

PACK="$HERE/exports/${1:?usage: $0 <export name> | --uninstall}/Localization"
[ -d "$PACK/XLIFF/zh-TW" ] || { echo "Not found: $PACK/XLIFF/zh-TW" >&2; exit 1; }

sudo rm -rf "$LOC/XLIFF/zh-TW"
sudo mkdir -p "$LOC/XLIFF/zh-TW"
sudo cp "$PACK/XLIFF/zh-TW/"*.xliff "$LOC/XLIFF/zh-TW/"
sudo cp "$PACK/CSV/"*_zh-TW.csv "$LOC/CSV/"
echo "Installed $(ls "$LOC/XLIFF/zh-TW" | wc -l | tr -d ' ') XLIFF files and the species CSV."
echo "Start /Applications/XWVM/xwvm-zhTW.app and choose Settings > Audio and Language > Language > Chinese (Traditional)."
