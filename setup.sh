#!/bin/bash
# Skill Manager - 总安装入口 (macOS/Linux)
# 用法: bash setup.sh

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEP_ERROR=0

# ============================================
# Step 0: 依赖检查（AI 可读格式）
# ============================================
echo "========================================"
echo "  Step 0: 环境依赖检查"
echo "========================================"

# --- Git ---
if command -v git &> /dev/null; then
    echo -e "\033[32m[DEP_CHECK] git: OK ($(git --version))\033[0m"
else
    echo -e "\033[31m[DEP_CHECK] git: MISSING\033[0m"
    echo -e "\033[33m[DEP_ACTION] macOS: brew install git | Ubuntu/Debian: sudo apt install git | CentOS: sudo yum install git\033[0m"
    DEP_ERROR=1
fi

# --- Node.js ---
if command -v node &> /dev/null; then
    echo -e "\033[32m[DEP_CHECK] node: OK ($(node --version))\033[0m"
else
    echo -e "\033[31m[DEP_CHECK] node: MISSING\033[0m"
    echo -e "\033[33m[DEP_ACTION] macOS: brew install node | Ubuntu: sudo apt install nodejs npm | 或访问 https://nodejs.org\033[0m"
    DEP_ERROR=1
fi

# --- npm ---
if command -v npm &> /dev/null; then
    echo -e "\033[32m[DEP_CHECK] npm: OK (v$(npm --version))\033[0m"
else
    echo -e "\033[31m[DEP_CHECK] npm: MISSING\033[0m"
    echo -e "\033[33m[DEP_ACTION] npm 随 Node.js 一起安装，请先安装 Node.js\033[0m"
    DEP_ERROR=1
fi

# --- npx ---
if command -v npx &> /dev/null; then
    echo -e "\033[32m[DEP_CHECK] npx: OK\033[0m"
else
    echo -e "\033[31m[DEP_CHECK] npx: MISSING\033[0m"
    echo -e "\033[33m[DEP_ACTION] 运行: npm install -g npx\033[0m"
    DEP_ERROR=1
fi

# --- Python ---
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "\033[32m[DEP_CHECK] python: OK ($(python3 --version 2>&1))\033[0m"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "\033[32m[DEP_CHECK] python: OK ($(python --version 2>&1))\033[0m"
else
    echo -e "\033[31m[DEP_CHECK] python: MISSING\033[0m"
    echo -e "\033[33m[DEP_ACTION] macOS: brew install python@3.12 | Ubuntu: sudo apt install python3\033[0m"
    DEP_ERROR=1
fi

echo ""
if [ $DEP_ERROR -eq 1 ]; then
    echo -e "\033[35m[DEP_RESULT] 有依赖缺失，请 AI 助手根据上面的 [DEP_ACTION] 自动安装后重新运行本脚本\033[0m"
    echo -e "\033[35m[DEP_RESULT] 也可以手动安装上述缺失项后重新运行: bash setup.sh\033[0m"
    exit 1
fi
echo -e "\033[32m[DEP_RESULT] 所有依赖满足 ✓\033[0m"
echo ""

# Step 1: 安装 skill-manager 到本地
echo "========================================"
echo "  Step 1: 安装 Skill Manager 本身"
echo "========================================"
SRC="$ROOT/skill-manager"
if [ ! -d "$SRC" ]; then
    echo "错误: 未找到 skill-manager 文件夹"
    exit 1
fi
DST1="$HOME/.agents/skills/skill-manager"
DST2="$HOME/.claude/skills/skill-manager"
mkdir -p "$(dirname "$DST1")"
mkdir -p "$(dirname "$DST2")"
cp -r "$SRC" "$DST1"
cp -r "$SRC" "$DST2" 2>/dev/null || true
echo "  skill-manager 已安装"

# Step 2: 运行批量安装
echo ""
echo "========================================"
echo "  Step 2: 安装 40 个科研 Skill"
echo "========================================"
INSTALL_SCRIPT="$ROOT/install_all.sh"
if [ -f "$INSTALL_SCRIPT" ]; then
    bash "$INSTALL_SCRIPT"
else
    echo "错误: 未找到 install_all.sh，正在用 install_all.ps1 的逻辑..."
    # Fallback: 直接在这里执行安装逻辑
    echo '[1/6] 安装 gemini-cli ...'
    npx skills add https://github.com/google-gemini/gemini-cli.git --skill 'code-reviewer' -y 2>&1 || true
    echo '  完成!'

    echo '[2/6] 安装 Chinese-Grant-Writer-Skills ...'
    npx skills add https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git --skill 'fund-background-writer fund-literature-review-writer fund-research-content-writer fund-technical-route-writer' -y 2>&1 || true
    echo '  完成!'

    echo '[3/6] 安装 nature-skills ...'
    npx skills add https://github.com/yuan1z0825/nature-skills.git --skill 'nature-academic-search nature-citation nature-data nature-downloader nature-figure nature-literature-pipeline nature-paper-to-patent nature-paper2ppt nature-polishing nature-reader nature-response nature-reviewer nature-writing researchwrite' -y 2>&1 || true
    echo '  完成!'

    echo '[4/6] 安装 paper-craft-skills ...'
    npx skills add https://github.com/zsyggg/paper-craft-skills.git --skill 'paper-analyzer paper-comic paper-deck' -y 2>&1 || true
    echo '  完成!'

    echo '[5/6] 安装 trending-skills ...'
    npx skills add https://github.com/aradotso/trending-skills.git --skill 'posterskill-academic-posters' -y 2>&1 || true
    echo '  完成!'

    echo '[6/6] 安装 PaperSpine...'
    if [ ! -d "$HOME/PaperSpine" ]; then
        git clone https://github.com/WUBING2023/PaperSpine.git "$HOME/PaperSpine" 2>&1 || true
    fi
    cd "$HOME/PaperSpine" && git pull 2>&1 || true
    bash install.sh --target all --clean-legacy 2>&1 || true
    echo '  完成!'
fi

# 完成
echo ""
echo "========================================"
echo "  全部完成！"
echo "  验证: $PYTHON_CMD ~/.agents/skills/skill-manager/scripts/skill_manager.py list"
echo "========================================"
