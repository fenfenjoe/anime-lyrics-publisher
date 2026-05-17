# GitHub仓库创建并推送脚本
# 在主机PowerShell中执行此脚本
# 请在环境变量中设置 GITHUB_TOKEN，或在此处填写你的 token

$token = $env:GITHUB_TOKEN  # 从环境变量读取
# 如果环境变量未设置，可以取消注释下面一行并填写你的 token
# $token = "your_github_personal_access_token_here"

$repo = "anime-lyrics-publisher"
$user = "fenfenjoe"
$projectPath = "E:\workspace\workbuddy\anime-lyrics-publisher"

Write-Host "=== GitHub 仓库创建并推送脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查 token 是否设置
if (-not $token) {
    Write-Host "错误: 请设置 GITHUB_TOKEN 环境变量或在脚本中填写 token" -ForegroundColor Red
    exit 1
}

# 检查远程仓库是否已添加
Set-Location $projectPath
$remoteExists = git remote get-url origin 2>$null

if ($remoteExists) {
    Write-Host "远程仓库已存在，跳过添加" -ForegroundColor Yellow
} else {
    Write-Host "添加远程仓库..." -ForegroundColor Cyan
    git remote add origin "https://$token@github.com/$user/$repo.git"
}

# 切换分支名称
Write-Host "切换分支名称到 main..." -ForegroundColor Cyan
git branch -M main

# 推送代码
Write-Host "推送代码到 GitHub..." -ForegroundColor Cyan
git push -u origin main

Write-Host ""
Write-Host "=== 完成！ ===" -ForegroundColor Green
Write-Host "仓库地址: https://github.com/$user/$repo" -ForegroundColor Green
