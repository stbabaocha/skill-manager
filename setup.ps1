# Skill Manager - 总安装入口
# 只需运行这一个脚本即可完成全部安装（AI 可自动处理缺失依赖）
# 用法: powershell -ExecutionPolicy Bypass -File setup.ps1

$root = $PSScriptRoot
$depError = $false

# ============================================
# Step 0: 依赖检查（AI 可读格式）
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 0: 环境依赖检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Git ---
$gitOk = $false
try { $null = Get-Command git -ErrorAction Stop; $gitVer = & git --version 2>$null; Write-Host "[DEP_CHECK] git: OK ($gitVer)" -ForegroundColor Green; $gitOk = $true } catch { Write-Host "[DEP_CHECK] git: MISSING" -ForegroundColor Red; Write-Host "[DEP_ACTION] 请安装 Git: winget install --id Git.Git -e --source winget" -ForegroundColor Yellow; $depError = $true }

# --- Node.js ---
$nodeOk = $false
try { $null = Get-Command node -ErrorAction Stop; $nodeVer = & node --version 2>$null; Write-Host "[DEP_CHECK] node: OK (v$nodeVer)" -ForegroundColor Green; $nodeOk = $true } catch { Write-Host "[DEP_CHECK] node: MISSING" -ForegroundColor Red; Write-Host "[DEP_ACTION] 请安装 Node.js: winget install --id OpenJS.NodeJS.LTS -e --source winget" -ForegroundColor Yellow; $depError = $true }

# --- npm ---
$npmOk = $false
try { $null = Get-Command npm -ErrorAction Stop; $npmVer = & npm --version 2>$null; Write-Host "[DEP_CHECK] npm: OK (v$npmVer)" -ForegroundColor Green; $npmOk = $true } catch { Write-Host "[DEP_CHECK] npm: MISSING" -ForegroundColor Red; Write-Host "[DEP_ACTION] npm 随 Node.js 一起安装，请先安装 Node.js" -ForegroundColor Yellow; $depError = $true }

# --- npx ---
$npxOk = $false
try { $null = Get-Command npx.cmd -ErrorAction Stop; Write-Host "[DEP_CHECK] npx: OK" -ForegroundColor Green; $npxOk = $true } catch { try { $null = Get-Command npx -ErrorAction Stop; Write-Host "[DEP_CHECK] npx: OK" -ForegroundColor Green; $npxOk = $true } catch { Write-Host "[DEP_CHECK] npx: MISSING" -ForegroundColor Red; Write-Host "[DEP_ACTION] 运行: npm install -g npx" -ForegroundColor Yellow; $depError = $true } }

# --- Python ---
$pythonOk = $false
try { $null = Get-Command python -ErrorAction Stop; $pyVer = & python --version 2>&1; Write-Host "[DEP_CHECK] python: OK ($pyVer)" -ForegroundColor Green; $pythonOk = $true } catch { try { $null = Get-Command python3 -ErrorAction Stop; $pyVer = & python3 --version 2>&1; Write-Host "[DEP_CHECK] python: OK ($pyVer)" -ForegroundColor Green; $pythonOk = $true } catch { Write-Host "[DEP_CHECK] python: MISSING" -ForegroundColor Red; Write-Host "[DEP_ACTION] 请安装 Python 3.8+: winget install --id Python.Python.3.12 -e --source winget" -ForegroundColor Yellow; $depError = $true } }

Write-Host ""
if ($depError) {
    Write-Host "[DEP_RESULT] 有依赖缺失，请 AI 助手根据上面的 [DEP_ACTION] 自动安装后重新运行本脚本" -ForegroundColor Magenta
    Write-Host "[DEP_RESULT] 也可以手动安装上述缺失项后重新运行: powershell -ExecutionPolicy Bypass -File setup.ps1" -ForegroundColor Magenta
    exit 1
}
Write-Host "[DEP_RESULT] 所有依赖满足 ✓" -ForegroundColor Green
Write-Host ""

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
