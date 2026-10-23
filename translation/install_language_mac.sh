#!/bin/sh
# Install a language pack built by `tools/localization_tool.py build --name <name>` into XWVM (macOS).
# The locale (zh-TW, ja, ko, ...) is taken from the pack's Localization/XLIFF/<locale> folder.
# XWVM's StreamingAssets folder is owned by root, so sudo asks for your password.
#
#   ./install_language_mac.sh <export name | export folder>   e.g. ./install_language_mac.sh zh-TW-v1
#                                                             or   ./install_language_mac.sh ../translation-ja/exports/ja-v1
#   ./install_language_mac.sh --uninstall <locale>            e.g. ./install_language_mac.sh --uninstall zh-TW
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
LOC="${XWVM_LOCALIZATION_DIR:-/Library/Application Support/XWVM Team/XWVM/StreamingAssets/Localization}"
[ -d "$LOC/XLIFF" ] || { echo "XWVM language folder not found: $LOC" >&2; exit 1; }
# The folder is normally owned by root; only ask for a password when it is not writable.
if [ -w "$LOC/XLIFF" ] && [ -w "$LOC/CSV" ]; then SUDO=""; else SUDO="sudo"; fi
USAGE="usage: $0 <export name | export folder> | --uninstall <locale>"

if [ "$1" = "--uninstall" ]; then
    LOCALE="${2:?$USAGE}"
    $SUDO rm -rf "$LOC/XLIFF/$LOCALE"
    $SUDO rm -f "$LOC/CSV/"*_"$LOCALE".csv
    echo "$LOCALE removed."
    exit 0
fi

ARG="${1:?$USAGE}"
if [ -d "$ARG/Localization" ]; then PACK="$ARG/Localization"; else PACK="$HERE/exports/$ARG/Localization"; fi
[ -d "$PACK/XLIFF" ] || { echo "Not a language pack: $PACK" >&2; exit 1; }
set -- "$PACK/XLIFF"/*/
[ $# -eq 1 ] && [ -d "$1" ] || { echo "Expected exactly one locale folder in $PACK/XLIFF" >&2; exit 1; }
LOCALE="$(basename "$1")"

$SUDO rm -rf "$LOC/XLIFF/$LOCALE"
$SUDO mkdir -p "$LOC/XLIFF/$LOCALE"
$SUDO cp "$PACK/XLIFF/$LOCALE/"*.xliff "$LOC/XLIFF/$LOCALE/"
$SUDO cp "$PACK/CSV/"*_"$LOCALE".csv "$LOC/CSV/"
echo "Installed $LOCALE: $(ls "$LOC/XLIFF/$LOCALE" | wc -l | tr -d ' ') XLIFF files and the species CSV."
echo "Start /Applications/XWVM/xwvm-zhTW.app and choose the language in Settings > Audio and Language > Language."
