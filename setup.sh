#!/bin/bash
# Skill Manager - 总安装入口 (macOS/Linux)
# 用法: bash setup.sh
# 支持完全新手：自动安装 Homebrew、Git、Node.js、Python

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[32m'; RED='\033[31m'; YELLOW='\033[33m'; CYAN='\033[36m'; RESET='\033[0m'

echo "========================================"
echo -e "${CYAN}  Step 0: 环境依赖检查 + 自动安装${RESET}"
echo "========================================"

# 检测操作系统
OS="$(uname -s)"
IS_MAC=false; IS_LINUX=false
case "$OS" in
    Darwin*) IS_MAC=true ;;
    Linux*)  IS_LINUX=true ;;
esac

# --- Homebrew (macOS only) ---
if $IS_MAC; then
    if command -v brew &> /dev/null; then
        echo -e "${GREEN}[DEP_CHECK] brew: OK$(${RESET})"
    else
        echo -e "${RED}[DEP_CHECK] brew: MISSING${RESET}"
        echo -e "${YELLOW}[DEP_ACTION] 正在自动安装 Homebrew...${RESET}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Apple Silicon 需要加 PATH
        if [ -f "/opt/homebrew/bin/brew" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile 2>/dev/null || true
        fi
        echo -e "${GREEN}[DEP_CHECK] brew: 安装成功 ✓${RESET}"
    fi
fi

# 通用依赖安装函数
install_dep() {
    local name="$1" cmd="$2" brew_pkg="$3" apt_pkg="$4"
    if command -v "$cmd" &> /dev/null; then
        local ver
        ver=$("$cmd" --version 2>&1 | head -1)
        echo -e "${GREEN}[DEP_CHECK] ${name}: OK (${ver})${RESET}"
        return 0
    fi
    echo -e "${RED}[DEP_CHECK] ${name}: MISSING${RESET}"
    echo -e "${YELLOW}[DEP_ACTION] 正在自动安装 ${name}...${RESET}"
    if $IS_MAC && command -v brew &> /dev/null; then
        brew install "$brew_pkg"
    elif $IS_LINUX; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y "$apt_pkg"
        elif command -v yum &> /dev/null; then
            sudo yum install -y "$apt_pkg"
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y "$apt_pkg"
        else
            echo -e "${RED}[DEP_ACTION] 无法自动安装 ${name}，请手动安装${RESET}"
            return 1
        fi
    fi
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}[DEP_CHECK] ${name}: 安装成功 ✓${RESET}"
        return 0
    else
        echo -e "${RED}[DEP_CHECK] ${name}: 安装失败，请手动安装${RESET}"
        return 1
    fi
}

DEP_ERROR=0

# Git
install_dep "git" "git" "git" "git" || DEP_ERROR=1

# Node.js + npm + npx
install_dep "node" "node" "node" "nodejs" || DEP_ERROR=1
# Linux 可能需要单独装 npm
if ! command -v npm &> /dev/null; then
    install_dep "npm" "npm" "npm" "npm" || DEP_ERROR=1
fi

# Python
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}[DEP_CHECK] python: OK ($(python3 --version 2>&1))${RESET}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}[DEP_CHECK] python: OK ($(python --version 2>&1))${RESET}"
else
    install_dep "python" "python3" "python@3.12" "python3" || DEP_ERROR=1
    PYTHON_CMD="python3"
fi

echo ""
if [ $DEP_ERROR -eq 1 ]; then
    echo -e "${RED}[DEP_RESULT] 有依赖安装失败，请手动安装后重新运行: bash setup.sh${RESET}"
    exit 1
fi
echo -e "${GREEN}[DEP_RESULT] 所有依赖满足 ✓${RESET}"
echo ""

# ============================================
# Step 1: 安装 skill-manager 到本地
# ============================================
echo "========================================"
echo -e "${CYAN}  Step 1: 安装 Skill Manager 本身${RESET}"
echo "========================================"

# 验证源目录
if [ ! -f "$ROOT/SKILL.md" ]; then
    echo -e "${RED}错误: 当前目录不是有效的 skill-manager 仓库（缺少 SKILL.md）${RESET}"
    exit 1
fi

DST1="$HOME/.agents/skills/skill-manager"
DST2="$HOME/.claude/skills/skill-manager"
mkdir -p "$DST1" "$DST2"

# 复制核心文件
cp -f "$ROOT/SKILL.md" "$DST1/"
cp -rf "$ROOT/scripts" "$DST1/"
cp -f "$ROOT/SKILL.md" "$DST2/" 2>/dev/null || true
cp -rf "$ROOT/scripts" "$DST2/" 2>/dev/null || true

echo -e "${GREEN}  skill-manager 已安装到:${RESET}"
echo "    $DST1"
echo "    $DST2"

# ============================================
# Step 2: 安装科研 Skill
# ============================================
echo ""
echo "========================================"
echo -e "${CYAN}  Step 2: 安装 40 个科研 Skill${RESET}"
echo "========================================"

INSTALL_SCRIPT="$ROOT/install_all.sh"
if [ -f "$INSTALL_SCRIPT" ]; then
    bash "$INSTALL_SCRIPT"
else
    echo -e "${YELLOW}未找到 install_all.sh，使用内置安装逻辑...${RESET}"

    echo '[1/8] 安装 gemini-cli (code-reviewer)...'
    npx skills add https://github.com/google-gemini/gemini-cli.git --skill 'code-reviewer' -y 2>&1 || true
    echo '  ✓'

    echo '[2/8] 安装 Chinese-Grant-Writer-Skills (4 个)...'
    npx skills add https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git --skill 'fund-background-writer fund-literature-review-writer fund-research-content-writer fund-technical-route-writer' -y 2>&1 || true
    echo '  ✓'

    echo '[3/8] 安装 nature-skills (14 个)...'
    npx skills add https://github.com/yuan1z0825/nature-skills.git --skill 'nature-academic-search nature-citation nature-data nature-downloader nature-figure nature-literature-pipeline nature-paper-to-patent nature-paper2ppt nature-polishing nature-reader nature-response nature-reviewer nature-writing researchwrite' -y 2>&1 || true
    echo '  ✓'

    echo '[4/8] 安装 paper-craft-skills (3 个)...'
    npx skills add https://github.com/zsyggg/paper-craft-skills.git --skill 'paper-analyzer paper-comic paper-deck' -y 2>&1 || true
    echo '  ✓'

    echo '[5/8] 安装 trending-skills (1 个)...'
    npx skills add https://github.com/aradotso/trending-skills.git --skill 'posterskill-academic-posters' -y 2>&1 || true
    echo '  ✓'

    echo '[6/8] 安装 PaperSpine (12 个)...'
    if [ ! -d "$HOME/PaperSpine" ]; then
        git clone https://github.com/WUBING2023/PaperSpine.git "$HOME/PaperSpine" 2>&1 || true
    fi
    cd "$HOME/PaperSpine" && git pull 2>&1 || true
    if [ -f "install.sh" ]; then
        bash install.sh --target all --clean-legacy 2>&1 || true
    fi
    echo '  ✓'

    echo '[7/8] Claude Code 插件需手动安装:'
    echo '  在 Claude Code 中运行: /plugin install academic-research-skills@academic-research-skills'

    echo '[8/8] 安装 token-saver...'
    npx skills add https://github.com/stbabaocha/skill-manager.git --skill 'token-saver' -y 2>&1 || true
    echo '  ✓'
fi

# ============================================
# 完成
# ============================================
echo ""
echo "========================================"
echo -e "${GREEN}  ✅ 全部完成！${RESET}"
echo ""
echo "  验证: $PYTHON_CMD ~/.agents/skills/skill-manager/scripts/skill_manager.py list --unique"
echo "  推荐: $PYTHON_CMD ~/.agents/skills/skill-manager/scripts/skill_manager.py recommend 我想写论文"
echo "========================================"
