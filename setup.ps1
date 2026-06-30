# Skill Manager - 总安装入口
# 只需运行这一个脚本即可完成全部安装
# 用法: powershell -ExecutionPolicy Bypass -File setup.ps1

$root = $PSScriptRoot

# Step 1: 安装 skill-manager 到本地
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 1: 安装 Skill Manager 本身" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$src = Join-Path $root "skill-manager"
if (-not (Test-Path $src)) {
    Write-Host "错误: 未找到 skill-manager 文件夹" -ForegroundColor Red
    exit 1
}
$dst1 = "$env:USERPROFILE\.agents\skills\skill-manager"
$dst2 = "$env:USERPROFILE\.claude\skills\skill-manager"
New-Item -ItemType Directory -Force -Path (Split-Path $dst1) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $dst2) | Out-Null
Copy-Item -Recurse -Force $src $dst1
Copy-Item -Recurse -Force $src $dst2 -ErrorAction SilentlyContinue
Write-Host "  skill-manager 已安装" -ForegroundColor Green

# Step 2: 运行批量安装
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 2: 安装 40 个科研 Skill" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$installScript = Join-Path $root "install_all.ps1"
if (Test-Path $installScript) {
    & $installScript
} else {
    Write-Host "错误: 未找到 install_all.ps1" -ForegroundColor Red
}

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  全部完成！" -ForegroundColor Green
Write-Host "  验证: python ~\.agents\skills\skill-manager\scripts\skill_manager.py list" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
