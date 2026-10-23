#!/bin/sh
# XWVM 繁體中文化 {{VERSION}} — macOS 移除程式（在 Finder 中雙擊執行）
# 刪除 xwvm-zhTW.app 與繁體中文語言包；原版 xwvm.app、存檔與設定都不受影響。
cd "$(dirname "$0")" || exit 1
HERE="$(pwd)"
FILES="$HERE/files"

finish() {
    echo
    printf "按 Enter 關閉這個視窗…"
    read _
    exit "$1"
}
fail() {
    echo
    echo "❌ $1"
    finish 1
}

xattr -dr com.apple.quarantine "$HERE" 2>/dev/null

echo "================================================"
echo "  XWVM 繁體中文化 {{VERSION}}  移除程式（macOS）"
echo "================================================"

DEST="${XWVM_ZH_APP:-/Applications/XWVM/xwvm-zhTW.app}"
if [ ! -d "$DEST" ]; then
    echo
    echo "在預設位置找不到 xwvm-zhTW.app，請在跳出的視窗中選擇它（若已刪除可按取消，只移除語言包）。"
    DEST="$(osascript -e 'POSIX path of (choose file with prompt "請選擇 xwvm-zhTW.app" of type {"com.apple.application-bundle"} default location (path to applications folder))' 2>/dev/null)"
    DEST="${DEST%/}"
fi

if [ -n "$DEST" ] && [ -d "$DEST" ]; then
    case "$(basename "$DEST")" in
        xwvm-zhTW.app) ;;
        *) fail "只能移除 xwvm-zhTW.app，不會刪除其他應用程式：$DEST" ;;
    esac
    echo
    echo "【1/2】刪除 $DEST …"
    if [ -w "$(dirname "$DEST")" ]; then
        sh "$FILES/install_mac.sh" --uninstall "$DEST" || fail "刪除失敗。"
    else
        echo "這個資料夾需要管理員權限，請輸入 Mac 登入密碼（輸入時畫面不會顯示）。"
        sudo sh "$FILES/install_mac.sh" --uninstall "$DEST" || fail "刪除失敗。"
    fi
fi

echo
echo "【2/2】移除繁體中文語言包 …"
echo "如果出現「Password:」，請輸入 Mac 登入密碼（輸入時畫面不會顯示）。"
sh "$FILES/install_language_mac.sh" --uninstall zh-TW || fail "移除語言包失敗。"

echo
echo "✅ 已移除。原版 XWVM（xwvm.app）、存檔與設定都沒有變動。"
finish 0
