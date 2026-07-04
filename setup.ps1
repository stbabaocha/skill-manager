# Skill Manager - 总安装入口 (Windows)
# 用法: powershell -ExecutionPolicy Bypass -File setup.ps1
# 支持完全新手：自动检测并安装缺失依赖

$root = $PSScriptRoot
$autoInstall = $true  # 自动安装缺失依赖

# ============================================
# Step 0: 依赖检查 + 自动安装
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 0: 环境依赖检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Test-Dep($name, $cmd, $installCmd, $installNote) {
    try {
        $null = Get-Command $cmd -ErrorAction Stop
        $ver = & $cmd --version 2>$null
        Write-Host "[DEP_CHECK] ${name}: OK ($ver)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[DEP_CHECK] ${name}: MISSING" -ForegroundColor Red
        if ($autoInstall) {
            Write-Host "[DEP_ACTION] 正在自动安装 ${name}..." -ForegroundColor Yellow
            try {
                Invoke-Expression $installCmd
                # 刷新 PATH
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
                $null = Get-Command $cmd -ErrorAction Stop
                Write-Host "[DEP_CHECK] ${name}: 安装成功 ✓" -ForegroundColor Green
                return $true
            } catch {
                Write-Host "[DEP_CHECK] ${name}: 自动安装失败" -ForegroundColor Red
                Write-Host "[DEP_ACTION] 请手动安装: $installNote" -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "[DEP_ACTION] $installNote" -ForegroundColor Yellow
            return $false
        }
    }
}

# 先检查 winget
$hasWinget = $false
try { $null = Get-Command winget -ErrorAction Stop; $hasWinget = $true } catch {}

$depOk = $true

# Git
if (-not (Test-Dep "git" "git" $(if ($hasWinget) { "winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements" } else { "echo '请手动安装 Git'" }) "winget install --id Git.Git -e --source winget")) { $depOk = $false }

# Node.js (npm/npx 随之安装)
if (-not (Test-Dep "node" "node" $(if ($hasWinget) { "winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements" } else { "echo '请手动安装 Node.js'" }) "winget install --id OpenJS.NodeJS.LTS -e --source winget")) { $depOk = $false }

# Python
$pythonOk = $false
try { $null = Get-Command python -ErrorAction Stop; $pythonOk = $true } catch {}
if (-not $pythonOk) {
    try { $null = Get-Command python3 -ErrorAction Stop; $pythonOk = $true } catch {}
}
if (-not $pythonOk) {
    $pythonOk = Test-Dep "python" "python" $(if ($hasWinget) { "winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements" } else { "echo '请手动安装 Python'" }) "winget install --id Python.Python.3.12 -e --source winget"
}

Write-Host ""
if (-not $depOk) {
    Write-Host "[DEP_RESULT] 有依赖安装失败，请根据上面的提示手动安装后重新运行：" -ForegroundColor Magenta
    Write-Host "  powershell -ExecutionPolicy Bypass -File setup.ps1" -ForegroundColor White
    exit 1
}
Write-Host "[DEP_RESULT] 所有依赖满足 ✓" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 1: 安装 skill-manager 到本地
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 1: 安装 Skill Manager 本身" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 仓库根目录就是 skill-manager（包含 SKILL.md + scripts/）
$src = $root

# 验证源目录
if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
    Write-Host "错误: 当前目录不是有效的 skill-manager 仓库（缺少 SKILL.md）" -ForegroundColor Red
    Write-Host "请确保你在 skill-manager 仓库根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

$dst1 = "$env:USERPROFILE\.agents\skills\skill-manager"
$dst2 = "$env:USERPROFILE\.claude\skills\skill-manager"
New-Item -ItemType Directory -Force -Path (Split-Path $dst1) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $dst2) | Out-Null

# 复制核心文件（排除 .git 等）
$filesToCopy = @("SKILL.md", "scripts")
foreach ($f in $filesToCopy) {
    $srcPath = Join-Path $src $f
    if (Test-Path $srcPath) {
        $dstPath1 = Join-Path $dst1 $f
        $dstPath2 = Join-Path $dst2 $f
        if ((Get-Item $srcPath).PSIsContainer) {
            Copy-Item -Recurse -Force $srcPath $dstPath1
            Copy-Item -Recurse -Force $srcPath $dstPath2 -ErrorAction SilentlyContinue
        } else {
            Copy-Item -Force $srcPath $dstPath1
            Copy-Item -Force $srcPath $dstPath2 -ErrorAction SilentlyContinue
        }
    }
}
Write-Host "  skill-manager 已安装到:" -ForegroundColor Green
Write-Host "    $dst1" -ForegroundColor Gray
Write-Host "    $dst2" -ForegroundColor Gray

# ============================================
# Step 2: 安装 40 个科研 Skill
# ============================================
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

# ============================================
# 完成
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 全部完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  验证命令：" -ForegroundColor White
Write-Host "    python $dst1\scripts\skill_manager.py list --unique" -ForegroundColor Gray
Write-Host ""
Write-Host "  快速开始：" -ForegroundColor White
Write-Host "    python $dst1\scripts\skill_manager.py recommend 我想写一篇论文" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Green
