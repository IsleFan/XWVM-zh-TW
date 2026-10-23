#!/bin/sh
# XWVM 繁體中文化 {{VERSION}} — macOS 安裝程式（在 Finder 中雙擊執行）
# 1. 在 XWVM 旁建立已加入中文字型外掛的 xwvm-zhTW.app（原版 xwvm.app 不會被修改）
# 2. 把繁體中文語言包放進 XWVM 的語言資料夾（需要輸入 Mac 登入密碼）
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

# 從網路下載的檔案會被標記為「隔離」，移除標記，避免安裝的檔案被 macOS 擋下。
xattr -dr com.apple.quarantine "$HERE" 2>/dev/null

echo "================================================"
echo "  XWVM 繁體中文化 {{VERSION}}  安裝程式（macOS）"
echo "================================================"

APP="${XWVM_APP:-/Applications/XWVM/xwvm.app}"
if [ ! -d "$APP/Contents/Resources/Data/Managed" ]; then
    echo
    echo "在預設位置找不到 XWVM，請在跳出的視窗中選擇 XWVM 應用程式（xwvm.app）。"
    APP="$(osascript -e 'POSIX path of (choose file with prompt "請選擇 XWVM 應用程式（xwvm.app）" of type {"com.apple.application-bundle"} default location (path to applications folder))' 2>/dev/null)" || fail "已取消安裝。"
    APP="${APP%/}"
fi
[ -d "$APP/Contents/Resources/Data/Managed" ] || fail "這不是 XWVM 應用程式：$APP"
DEST="$(dirname "$APP")/xwvm-zhTW.app"
echo
echo "找到 XWVM：$APP（版本 $(defaults read "$APP/Contents/Info" CFBundleShortVersionString 2>/dev/null)）"

echo
echo "【1/2】建立中文版遊戲 xwvm-zhTW.app …"
if [ -w "$(dirname "$APP")" ]; then
    sh "$FILES/install_mac.sh" "$APP" "$DEST" || fail "建立 xwvm-zhTW.app 失敗。"
else
    echo "這個資料夾需要管理員權限，請輸入 Mac 登入密碼（輸入時畫面不會顯示，輸入完按 Enter）。"
    sudo sh "$FILES/install_mac.sh" "$APP" "$DEST" || fail "建立 xwvm-zhTW.app 失敗。"
fi

echo
echo "【2/2】安裝繁體中文語言包 …"
echo "如果出現「Password:」，請輸入 Mac 登入密碼（輸入時畫面不會顯示，輸入完按 Enter）。"
sh "$FILES/install_language_mac.sh" "$FILES/zh-TW-v1" || fail "安裝語言包失敗。"

echo
echo "✅ 安裝完成！"
echo
echo "以後請用「xwvm-zhTW」開遊戲（位置：$DEST）。"
echo "第一次進遊戲：Settings → Audio and Language → Subtitles and Language → Language"
echo "選「Chinese (Traditional)」。"
echo
echo "XWVM 更新後，請重新執行一次這個安裝程式。"
open -R "$DEST" 2>/dev/null
finish 0
