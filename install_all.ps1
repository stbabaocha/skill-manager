# Skill Manager - 一键安装脚本
# 生成时间: 2026-06-30T17:20:05.528769
# 用法: powershell -ExecutionPolicy Bypass -File install_all.ps1

Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Skill Manager - 一键安装 40 个科研 Skill' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

# ===== 第 1 步: 安装 skill-manager 本身 =====
Write-Host '[1/6] 安装 skill-manager...' -ForegroundColor Yellow
$managerDir = "$env:USERPROFILE\.agents\skills\skill-manager"
if (-not (Test-Path $managerDir)) {
    Write-Host '  请先确保 skill-manager 已就位' -ForegroundColor Red
    Write-Host '  git clone 本仓库后，复制 skill-manager 目录到 ~\.agents\skills\' 
}

# ===== 第 2 步 =====
Write-Host '[2/6] 安装 gemini-cli ...' -ForegroundColor Yellow
Write-Host '  -> code-reviewer' -ForegroundColor Gray
npx.cmd skills add https://github.com/google-gemini/gemini-cli.git --skill 'code-reviewer' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 第 3 步 =====
Write-Host '[3/6] 安装 Chinese-Grant-Writer-Skills ...' -ForegroundColor Yellow
Write-Host '  -> fund-background-writer' -ForegroundColor Gray
Write-Host '  -> fund-literature-review-writer' -ForegroundColor Gray
Write-Host '  -> fund-research-content-writer' -ForegroundColor Gray
Write-Host '  -> fund-technical-route-writer' -ForegroundColor Gray
npx.cmd skills add https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git --skill 'fund-background-writer fund-literature-review-writer fund-research-content-writer fund-technical-route-writer' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 第 4 步 =====
Write-Host '[4/6] 安装 nature-skills ...' -ForegroundColor Yellow
Write-Host '  -> nature-academic-search' -ForegroundColor Gray
Write-Host '  -> nature-citation' -ForegroundColor Gray
Write-Host '  -> nature-data' -ForegroundColor Gray
Write-Host '  -> nature-downloader' -ForegroundColor Gray
Write-Host '  -> nature-figure' -ForegroundColor Gray
Write-Host '  -> nature-literature-pipeline' -ForegroundColor Gray
Write-Host '  -> nature-paper-to-patent' -ForegroundColor Gray
Write-Host '  -> nature-paper2ppt' -ForegroundColor Gray
Write-Host '  -> nature-polishing' -ForegroundColor Gray
Write-Host '  -> nature-reader' -ForegroundColor Gray
Write-Host '  -> nature-response' -ForegroundColor Gray
Write-Host '  -> nature-reviewer' -ForegroundColor Gray
Write-Host '  -> nature-writing' -ForegroundColor Gray
Write-Host '  -> researchwrite' -ForegroundColor Gray
npx.cmd skills add https://github.com/yuan1z0825/nature-skills.git --skill 'nature-academic-search nature-citation nature-data nature-downloader nature-figure nature-literature-pipeline nature-paper-to-patent nature-paper2ppt nature-polishing nature-reader nature-response nature-reviewer nature-writing researchwrite' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 第 5 步 =====
Write-Host '[5/6] 安装 paper-craft-skills ...' -ForegroundColor Yellow
Write-Host '  -> paper-analyzer' -ForegroundColor Gray
Write-Host '  -> paper-comic' -ForegroundColor Gray
Write-Host '  -> paper-deck' -ForegroundColor Gray
npx.cmd skills add https://github.com/zsyggg/paper-craft-skills.git --skill 'paper-analyzer paper-comic paper-deck' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 第 6 步 =====
Write-Host '[6/6] 安装 trending-skills ...' -ForegroundColor Yellow
Write-Host '  -> posterskill-academic-posters' -ForegroundColor Gray
npx.cmd skills add https://github.com/aradotso/trending-skills.git --skill 'posterskill-academic-posters' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 第 7 步: PaperSpine =====
Write-Host '[7/6] 安装 PaperSpine...' -ForegroundColor Yellow
if (-not (Test-Path $env:USERPROFILE\PaperSpine)) {
    git clone https://github.com/WUBING2023/PaperSpine.git $env:USERPROFILE\PaperSpine 2>&1 | Out-Null
}
cd $env:USERPROFILE\PaperSpine
git pull 2>&1 | Out-Null
powershell -ExecutionPolicy Bypass -File install.ps1 -Target all -CleanLegacy 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 第 8 步: Academic Research Skills (Claude Code 插件) =====
Write-Host '[8/6] Claude Code 插件需手动安装:' -ForegroundColor Yellow
Write-Host '  在 Claude Code 中运行: /plugin install academic-research-skills@academic-research-skills' -ForegroundColor White

# ===== 完成 =====
Write-Host ''
Write-Host '========================================' -ForegroundColor Green
Write-Host '  全部安装完成!' -ForegroundColor Green
Write-Host '  运行: python ~\.agents\skills\skill-manager\scripts\skill_manager.py list' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
