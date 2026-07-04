#!/bin/bash
# Skill Manager - 一键安装 40 个科研 Skill (macOS/Linux)
# 由 setup.sh 自动调用

GREEN='\033[32m'; YELLOW='\033[33m'; GRAY='\033[90m'; RESET='\033[0m'

echo '========================================'
echo -e "${YELLOW}  一键安装 40 个科研 Skill${RESET}"
echo '========================================'
echo ''

echo -e "${YELLOW}[1/8] 安装 gemini-cli...${RESET}"
echo -e "${GRAY}  -> code-reviewer${RESET}"
npx skills add https://github.com/google-gemini/gemini-cli.git --skill 'code-reviewer' -y 2>&1 || true
echo -e "${GREEN}  完成!${RESET}"

echo -e "${YELLOW}[2/8] 安装 Chinese-Grant-Writer-Skills...${RESET}"
echo -e "${GRAY}  -> fund-background-writer${RESET}"
echo -e "${GRAY}  -> fund-literature-review-writer${RESET}"
echo -e "${GRAY}  -> fund-research-content-writer${RESET}"
echo -e "${GRAY}  -> fund-technical-route-writer${RESET}"
npx skills add https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git --skill 'fund-background-writer fund-literature-review-writer fund-research-content-writer fund-technical-route-writer' -y 2>&1 || true
echo -e "${GREEN}  完成!${RESET}"

echo -e "${YELLOW}[3/8] 安装 nature-skills...${RESET}"
echo -e "${GRAY}  -> nature-academic-search, nature-citation, nature-data, nature-downloader${RESET}"
echo -e "${GRAY}  -> nature-figure, nature-literature-pipeline, nature-paper-to-patent${RESET}"
echo -e "${GRAY}  -> nature-paper2ppt, nature-polishing, nature-reader${RESET}"
echo -e "${GRAY}  -> nature-response, nature-reviewer, nature-writing, researchwrite${RESET}"
npx skills add https://github.com/yuan1z0825/nature-skills.git --skill 'nature-academic-search nature-citation nature-data nature-downloader nature-figure nature-literature-pipeline nature-paper-to-patent nature-paper2ppt nature-polishing nature-reader nature-response nature-reviewer nature-writing researchwrite' -y 2>&1 || true
echo -e "${GREEN}  完成!${RESET}"

echo -e "${YELLOW}[4/8] 安装 paper-craft-skills...${RESET}"
echo -e "${GRAY}  -> paper-analyzer, paper-comic, paper-deck${RESET}"
npx skills add https://github.com/zsyggg/paper-craft-skills.git --skill 'paper-analyzer paper-comic paper-deck' -y 2>&1 || true
echo -e "${GREEN}  完成!${RESET}"

echo -e "${YELLOW}[5/8] 安装 trending-skills...${RESET}"
echo -e "${GRAY}  -> posterskill-academic-posters${RESET}"
npx skills add https://github.com/aradotso/trending-skills.git --skill 'posterskill-academic-posters' -y 2>&1 || true
echo -e "${GREEN}  完成!${RESET}"

echo -e "${YELLOW}[6/8] 安装 PaperSpine...${RESET}"
if [ ! -d "$HOME/PaperSpine" ]; then
    git clone https://github.com/WUBING2023/PaperSpine.git "$HOME/PaperSpine" 2>&1 || true
fi
cd "$HOME/PaperSpine" && git pull 2>&1 || true
if [ -f "install.sh" ]; then
    bash install.sh --target all --clean-legacy 2>&1 || true
fi
echo -e "${GREEN}  完成!${RESET}"

echo -e "${YELLOW}[7/8] Claude Code 插件需手动安装:${RESET}"
echo '  在 Claude Code 中运行: /plugin install academic-research-skills@academic-research-skills'

echo -e "${YELLOW}[8/8] 安装 token-saver...${RESET}"
npx skills add https://github.com/stbabaocha/skill-manager.git --skill 'token-saver' -y 2>&1 || true
echo -e "${GREEN}  完成!${RESET}"

echo ''
echo '========================================'
echo -e "${GREEN}  全部安装完成!${RESET}"
echo '========================================'
