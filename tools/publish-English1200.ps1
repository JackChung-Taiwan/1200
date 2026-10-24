# English 1200 project publishing helper for Windows PowerShell 5.1+
# Place this script beside English1200_Website_Project(1).zip and run it after installing Git for Windows.
param(
    [string]$ZipPath = (Join-Path $PSScriptRoot 'English1200_Website_Project(1).zip')
)
$ErrorActionPreference = 'Stop'
$repoUrl = 'https://github.com/JackChung-Taiwan/1200.git'
$branch = 'main'
if (-not (Test-Path -LiteralPath $ZipPath -PathType Leaf)) {
    throw "找不到 ZIP：$ZipPath。請將本腳本與 English1200_Website_Project(1).zip 放在同一資料夾，或傳入 -ZipPath。"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw '找不到 Git。請先安裝 Git for Windows（https://git-scm.com/downloads/win），重新開啟 PowerShell 後再執行。'
}
$jobRoot = Join-Path $env:TEMP ('english1200-github-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$unzipDir = Join-Path $jobRoot 'unzipped'
$gitDir = Join-Path $jobRoot 'repo'
New-Item -ItemType Directory -Path $unzipDir -Force | Out-Null
Write-Host '[1/5] 解壓縮完整英語 1200 教材...'
Expand-Archive -LiteralPath $ZipPath -DestinationPath $unzipDir -Force
$source = Join-Path $unzipDir 'English1200_Website_Project'
if (-not (Test-Path -LiteralPath (Join-Path $source 'dist/index.html'))) {
    throw 'ZIP 結構不符：找不到 English1200_Website_Project/dist/index.html'
}
$mp3Count = @(Get-ChildItem -LiteralPath (Join-Path $source 'dist/original/English1200-0514') -Recurse -File -Filter '*.mp3').Count
if ($mp3Count -ne 2468) {
    throw "MP3 數量不符：預期 2468，實際 $mp3Count。為避免上傳不完整教材，已停止。"
}
Write-Host "已找到 $mp3Count 個 MP3。"
Write-Host '[2/5] 下載 GitHub 儲存庫...'
& git clone --branch $branch $repoUrl $gitDir
if ($LASTEXITCODE -ne 0) { throw 'GitHub clone 失敗，請檢查網路及帳號權限。' }
Write-Host '[3/5] 複製完整網站及原始教材（包含音檔）...'
Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $gitDir -Recurse -Force
}
Write-Host '[4/5] Git 提交變更...'
& git -C $gitDir add --all
if ($LASTEXITCODE -ne 0) { throw 'git add 失敗。' }
$changes = & git -C $gitDir status --porcelain
if (-not $changes) {
    Write-Host '沒有新變更，已經是最新版本。'
} else {
    & git -C $gitDir -c user.name='JackChung-Taiwan' -c user.email='JackChung-Taiwan@users.noreply.github.com' commit -m 'feat: publish English 1200 website with original audio and assets'
    if ($LASTEXITCODE -ne 0) { throw 'Git commit 失敗。' }
}
Write-Host '[5/5] 將網站與音檔推送至 GitHub...'
& git -C $gitDir push origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "保留本機工作副本：$gitDir"
    throw 'Git push 失敗。請登入 GitHub，確認 Git Credential Manager 權限後重新操作。'
}
Write-Host ''
Write-Host '上傳完成：https://github.com/JackChung-Taiwan/1200' -ForegroundColor Green
Write-Host '下一步：在 GitHub Settings -> Pages 中將 Source 設為 GitHub Actions。'
Write-Host '完成部署後網址：https://jackchung-taiwan.github.io/1200/'
Write-Host "本機工作副本：$gitDir"