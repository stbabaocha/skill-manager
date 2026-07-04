# Skill Manager - 一键安装 40 个科研 Skill (Windows)
# 由 setup.ps1 自动调用
# 用法: powershell -ExecutionPolicy Bypass -File install_all.ps1

Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  一键安装 40 个科研 Skill' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

# ===== [1/8] =====
Write-Host '[1/8] 安装 gemini-cli...' -ForegroundColor Yellow
Write-Host '  -> code-reviewer' -ForegroundColor Gray
npx.cmd skills add https://github.com/google-gemini/gemini-cli.git --skill 'code-reviewer' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== [2/8] =====
Write-Host '[2/8] 安装 Chinese-Grant-Writer-Skills...' -ForegroundColor Yellow
Write-Host '  -> fund-background-writer' -ForegroundColor Gray
Write-Host '  -> fund-literature-review-writer' -ForegroundColor Gray
Write-Host '  -> fund-research-content-writer' -ForegroundColor Gray
Write-Host '  -> fund-technical-route-writer' -ForegroundColor Gray
npx.cmd skills add https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git --skill 'fund-background-writer fund-literature-review-writer fund-research-content-writer fund-technical-route-writer' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== [3/8] =====
Write-Host '[3/8] 安装 nature-skills...' -ForegroundColor Yellow
Write-Host '  -> nature-academic-search, nature-citation, nature-data, nature-downloader' -ForegroundColor Gray
Write-Host '  -> nature-figure, nature-literature-pipeline, nature-paper-to-patent' -ForegroundColor Gray
Write-Host '  -> nature-paper2ppt, nature-polishing, nature-reader' -ForegroundColor Gray
Write-Host '  -> nature-response, nature-reviewer, nature-writing, researchwrite' -ForegroundColor Gray
npx.cmd skills add https://github.com/yuan1z0825/nature-skills.git --skill 'nature-academic-search nature-citation nature-data nature-downloader nature-figure nature-literature-pipeline nature-paper-to-patent nature-paper2ppt nature-polishing nature-reader nature-response nature-reviewer nature-writing researchwrite' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== [4/8] =====
Write-Host '[4/8] 安装 paper-craft-skills...' -ForegroundColor Yellow
Write-Host '  -> paper-analyzer, paper-comic, paper-deck' -ForegroundColor Gray
npx.cmd skills add https://github.com/zsyggg/paper-craft-skills.git --skill 'paper-analyzer paper-comic paper-deck' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== [5/8] =====
Write-Host '[5/8] 安装 trending-skills...' -ForegroundColor Yellow
Write-Host '  -> posterskill-academic-posters' -ForegroundColor Gray
npx.cmd skills add https://github.com/aradotso/trending-skills.git --skill 'posterskill-academic-posters' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== [6/8] =====
Write-Host '[6/8] 安装 PaperSpine...' -ForegroundColor Yellow
if (-not (Test-Path $env:USERPROFILE\PaperSpine)) {
    git clone https://github.com/WUBING2023/PaperSpine.git $env:USERPROFILE\PaperSpine 2>&1 | Out-Null
}
Push-Location $env:USERPROFILE\PaperSpine
git pull 2>&1 | Out-Null
if (Test-Path install.ps1) {
    powershell -ExecutionPolicy Bypass -File install.ps1 -Target all -CleanLegacy 2>&1 | Out-Null
}
Pop-Location
Write-Host '  完成!' -ForegroundColor Green

# ===== [7/8] =====
Write-Host '[7/8] Claude Code 插件需手动安装:' -ForegroundColor Yellow
Write-Host '  在 Claude Code 中运行: /plugin install academic-research-skills@academic-research-skills' -ForegroundColor White

# ===== [8/8] =====
Write-Host '[8/8] 安装 token-saver...' -ForegroundColor Yellow
npx.cmd skills add https://github.com/stbabaocha/skill-manager.git --skill 'token-saver' -y 2>&1 | Out-Null
Write-Host '  完成!' -ForegroundColor Green

# ===== 完成 =====
Write-Host ''
Write-Host '========================================' -ForegroundColor Green
Write-Host '  全部安装完成!' -ForegroundColor Green
Write-Host '  运行: python ~\.agents\skills\skill-manager\scripts\skill_manager.py list --unique' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
