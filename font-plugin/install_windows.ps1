<#
XWVM CJK font plugin + language pack installer for Windows.
Uses only Windows PowerShell 5.1 (built into Windows 10/11); no Python or .NET SDK needed.

  install_windows.ps1 [-GameDir <XWVM folder>] [-LanguagePack <export folder>] [-Uninstall]

Install:   copies XwvmChineseFont.dll (+ XwvmChineseFont-*.json, .ini, fonts folder) into <Game>_Data\Managed,
           registers it in ScriptingAssemblies.json / RuntimeInitializeOnLoads.json (originals kept as *.orig),
           and copies the language pack (Localization\XLIFF\<locale>, CSV\*_<locale>.csv) into XWVM's StreamingAssets.
Uninstall: removes all of the above. Running install again (e.g. after an XWVM update) is safe.
#>
param(
    [string]$GameDir,
    [string]$LanguagePack,
    [switch]$Uninstall,
    [switch]$Elevated
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Assembly = 'XwvmChineseFont'

function Finish([int]$code) {
    # The elevated window closes by itself, so let the user read the result first.
    if ($Elevated) { Read-Host '按 Enter 關閉' | Out-Null }
    exit $code
}

function Fail([string]$message) {
    Write-Host ''
    Write-Host "[錯誤] $message" -ForegroundColor Red
    Finish 1
}

function Get-DataDir([string]$dir) {
    if (-not $dir -or -not (Test-Path -LiteralPath $dir -PathType Container)) { return $null }
    foreach ($d in Get-ChildItem -LiteralPath $dir -Directory -Filter '*_Data') {
        if ((Test-Path -LiteralPath (Join-Path $d.FullName 'Managed\Assembly-CSharp.dll')) -and
            (Test-Path -LiteralPath (Join-Path $d.FullName 'ScriptingAssemblies.json'))) {
            return $d.FullName
        }
    }
    return $null
}

function Find-GameDir {
    $candidates = @(
        "$env:ProgramFiles\XWVM", "${env:ProgramFiles(x86)}\XWVM", "$env:LOCALAPPDATA\Programs\XWVM",
        "$env:USERPROFILE\XWVM", "$env:USERPROFILE\Desktop\XWVM", "$env:USERPROFILE\Downloads\XWVM",
        "$env:USERPROFILE\Documents\XWVM", 'C:\XWVM', 'C:\Games\XWVM', 'D:\XWVM', 'D:\Games\XWVM'
    )
    foreach ($c in $candidates) {
        if (Get-DataDir $c) { return $c }
    }
    Write-Host '在常見位置找不到 XWVM，請在跳出的視窗中選擇 XWVM 的安裝資料夾（裡面有 XWVM.exe）。'
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = '請選擇 XWVM 的安裝資料夾（裡面有 XWVM.exe 與 XWVM_Data）'
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return $null }
    return $dialog.SelectedPath
}

# XWVM reads its language files from StreamingAssets; on macOS that folder lives outside the app,
# so look in the usual Windows places as well as inside the game folder.
function Find-LocalizationDir([string]$game, [string]$data) {
    $candidates = @(
        "$data\StreamingAssets\Localization",
        "$env:ProgramData\XWVM Team\XWVM\StreamingAssets\Localization",
        "$env:LOCALAPPDATA\XWVM Team\XWVM\StreamingAssets\Localization",
        "$env:APPDATA\XWVM Team\XWVM\StreamingAssets\Localization"
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath "$c\XLIFF\en") { return $c }
    }
    foreach ($root in @($game, "$env:ProgramData\XWVM Team")) {
        if (Test-Path -LiteralPath $root) {
            $hit = Get-ChildItem -LiteralPath $root -Recurse -Directory -Filter 'en' -ErrorAction SilentlyContinue |
                Where-Object { $_.Parent.Name -eq 'XLIFF' } | Select-Object -First 1
            if ($hit) { return $hit.Parent.Parent.FullName }
        }
    }
    return $null
}

function Test-Writable([string]$dir) {
    try {
        $probe = Join-Path $dir ('.xwvm-write-test-' + [guid]::NewGuid())
        [IO.File]::WriteAllText($probe, 'x')
        Remove-Item -LiteralPath $probe -Force
        return $true
    } catch {
        return $false
    }
}

function Read-Json([string]$path) {
    return [IO.File]::ReadAllText($path) | ConvertFrom-Json
}

function Write-Json([string]$path, $value) {
    $json = $value | ConvertTo-Json -Depth 10 -Compress
    [IO.File]::WriteAllText($path, $json, (New-Object Text.UTF8Encoding($false)))
}

function Register-Plugin([string]$data, [bool]$remove) {
    $assembliesPath = Join-Path $data 'ScriptingAssemblies.json'
    $initPath = Join-Path $data 'RuntimeInitializeOnLoads.json'
    foreach ($path in @($assembliesPath, $initPath)) {
        if (-not (Test-Path -LiteralPath "$path.orig")) { Copy-Item -LiteralPath $path -Destination "$path.orig" }
    }
    $assemblies = Read-Json $assembliesPath
    $inits = Read-Json $initPath

    # Remove any previous registration first so the result is identical on every run.
    $dll = "$Assembly.dll"
    $names = New-Object System.Collections.ArrayList
    $types = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $assemblies.names.Count; $i++) {
        if ($assemblies.names[$i] -ne $dll) {
            [void]$names.Add($assemblies.names[$i])
            [void]$types.Add($assemblies.types[$i])
        }
    }
    $root = New-Object System.Collections.ArrayList
    foreach ($entry in $inits.root) {
        if ($entry.assemblyName -ne $Assembly) { [void]$root.Add($entry) }
    }

    if (-not $remove) {
        [void]$names.Add($dll)
        [void]$types.Add(16)  # user assembly
        [void]$root.Add([pscustomobject][ordered]@{
            assemblyName = $Assembly; nameSpace = 'XwvmChineseFont'; className = 'FallbackFontLoader'
            methodName = 'Init'; loadTypes = 1; isUnityClass = $false  # 1 = BeforeSceneLoad
        })
    }
    $assemblies.names = $names.ToArray()
    $assemblies.types = $types.ToArray()
    $inits.root = $root.ToArray()
    Write-Json $assembliesPath $assemblies
    Write-Json $initPath $inits
    if ($remove) {
        Remove-Item -LiteralPath "$assembliesPath.orig", "$initPath.orig" -Force -ErrorAction SilentlyContinue
    }
}

Write-Host '================================================'
Write-Host '  XWVM 繁體中文化  安裝程式（Windows）'
Write-Host '================================================'

# --- Locate the game -------------------------------------------------------------------------
if (-not $GameDir) { $GameDir = Find-GameDir }
if (-not $GameDir) { Fail '已取消。' }
$GameDir = $GameDir.TrimEnd('\')
if (Test-Path -LiteralPath (Join-Path $GameDir 'GameAssembly.dll')) {
    Fail '這個 XWVM 是 IL2CPP 版本，外掛無法載入。請到專案網站回報你的 XWVM 版本。'
}
$data = Get-DataDir $GameDir
if (-not $data) { Fail "這個資料夾不是 XWVM：$GameDir（找不到 *_Data\Managed\Assembly-CSharp.dll）" }
$managed = Join-Path $data 'Managed'
$localization = Find-LocalizationDir $GameDir $data
Write-Host ''
Write-Host "XWVM 資料夾：$GameDir"
Write-Host "語言檔資料夾：$(if ($localization) { $localization } else { '（找不到）' })"

# --- Ask for administrator rights only when a folder is not writable -------------------------
$needsAdmin = (-not (Test-Writable $managed)) -or ($localization -and -not (Test-Writable (Join-Path $localization 'XLIFF')))
if ($needsAdmin) {
    if ($Elevated) { Fail '即使以系統管理員身分執行仍無法寫入遊戲資料夾。' }
    Write-Host ''
    Write-Host '遊戲資料夾需要系統管理員權限，請在接下來跳出的視窗按「是」。' -ForegroundColor Yellow
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-GameDir', "`"$GameDir`"", '-Elevated')
    if ($LanguagePack) { $arguments += @('-LanguagePack', "`"$($LanguagePack.TrimEnd('\'))`"") }
    if ($Uninstall) { $arguments += '-Uninstall' }
    try {
        $process = Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    } catch {
        Fail '沒有取得系統管理員權限，已取消。'
    }
    exit $process.ExitCode
}

# --- Plugin ----------------------------------------------------------------------------------
Write-Host ''
Write-Host $(if ($Uninstall) { '【1/2】移除中文字型外掛 …' } else { '【1/2】安裝中文字型外掛 …' })
Get-ChildItem -LiteralPath $managed -Filter "$Assembly-*.json" | Remove-Item -Force
if ($Uninstall) {
    Remove-Item -LiteralPath (Join-Path $managed "$Assembly.dll"), (Join-Path $managed "$Assembly.ini") -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $managed "$Assembly-fonts") -Recurse -Force -ErrorAction SilentlyContinue
    Register-Plugin $data $true
} else {
    $sources = @(Get-Item -LiteralPath (Join-Path $Here "$Assembly.dll")) + @(Get-ChildItem -LiteralPath $Here -Filter "$Assembly-*.json")
    $ini = Join-Path $Here "$Assembly.ini"
    if (Test-Path -LiteralPath $ini) { $sources += Get-Item -LiteralPath $ini }
    foreach ($file in $sources) {
        Copy-Item -LiteralPath $file.FullName -Destination $managed -Force
        Unblock-File -LiteralPath (Join-Path $managed $file.Name)
    }
    $fonts = Join-Path $Here "$Assembly-fonts"
    if (Test-Path -LiteralPath $fonts) { Copy-Item -LiteralPath $fonts -Destination $managed -Recurse -Force }
    Register-Plugin $data $false
}

# --- Language pack ---------------------------------------------------------------------------
Write-Host ''
Write-Host $(if ($Uninstall) { '【2/2】移除語言包 …' } else { '【2/2】安裝語言包 …' })
if ($LanguagePack) {
    $xliffRoot = Join-Path $LanguagePack 'Localization\XLIFF'
    $locales = @(Get-ChildItem -LiteralPath $xliffRoot -Directory)
    if ($locales.Count -ne 1) { Fail "語言包格式不正確：$LanguagePack" }
    $locale = $locales[0].Name
    if (-not $localization) {
        Write-Host '找不到 XWVM 的語言檔資料夾（Localization\XLIFF\en），無法處理語言包。' -ForegroundColor Yellow
        Write-Host '請到專案網站回報你的 XWVM 安裝方式；安裝時也可以手動把 files 裡 Localization 的 XLIFF\<語系> 與 CSV 檔複製到 XWVM 的 StreamingAssets\Localization。'
        Finish 1
    }
    $target = Join-Path $localization "XLIFF\$locale"
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
    Get-ChildItem -LiteralPath (Join-Path $localization 'CSV') -Filter "*_$locale.csv" -ErrorAction SilentlyContinue | Remove-Item -Force
    if (-not $Uninstall) {
        New-Item -ItemType Directory -Path $target | Out-Null
        Copy-Item -Path (Join-Path $xliffRoot "$locale\*.xliff") -Destination $target
        Copy-Item -Path (Join-Path $LanguagePack "Localization\CSV\*_$locale.csv") -Destination (Join-Path $localization 'CSV')
    }
}

Write-Host ''
if ($Uninstall) {
    Write-Host '完成：已移除中文化，遊戲恢復原狀（存檔與設定不受影響）。' -ForegroundColor Green
} else {
    Write-Host '完成：已安裝中文化！' -ForegroundColor Green
    Write-Host ''
    Write-Host '照平常方式開啟 XWVM，第一次進遊戲到'
    Write-Host '  Settings > Audio and Language > Subtitles and Language > Language'
    Write-Host '選「Chinese (Traditional)」。'
    Write-Host ''
    Write-Host 'XWVM 更新後，請重新執行一次安裝程式。'
}
Finish 0
