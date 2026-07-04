# Skill Manager — 科研 Agent Skill 统一管理器

[![Skills](https://img.shields.io/badge/skills-40-blue)](https://github.com)
[![Platforms](https://img.shields.io/badge/platforms-7-green)]()

**一键安装 · 统一管理 · 多角度交叉验证 · 智能工作流推荐**

管理 GitHub Copilot、Claude Code、Cline、Codex 等平台上 **40 个科研 Agent Skill** 的命令行工具。

---

## 🚀 快速开始

### 🤖 AI 一键安装（推荐）

**把下面这段话复制粘贴到任意 AI 编程助手**（Copilot / Claude Code / Cline / Codex / Gemini CLI / Continue 均可），AI 会自动完成一切：

---

> 请帮我安装 skill-manager（40 个科研 AI Skill 的统一管理器）：
>
> 1. 克隆仓库：`git clone https://github.com/stbabaocha/skill-manager.git`，如果已存在则 `git pull`
> 2. 进入目录并运行安装脚本：
>    - **Windows**：`powershell -ExecutionPolicy Bypass -File setup.ps1`
>    - **macOS / Linux**：`bash setup.sh`
> 3. **重要**：如果脚本报 `[DEP_CHECK] ... MISSING` 错误，请根据 `[DEP_ACTION]` 的提示自动安装缺失的依赖（git/node/npm/python），然后重新运行安装脚本
> 4. 安装完成后运行验证：`python ~/.agents/skills/skill-manager/scripts/skill_manager.py list`

---

> 💡 **上面这段是写给你的 AI 助手看的，直接发过去即可。** AI 会自动检测操作系统、检查依赖、安装缺失项、完成全部 40 个 skill 安装。全程无需手动操作。

### 🖥️ 手动安装（终端）

**Windows:**
```powershell
git clone https://github.com/stbabaocha/skill-manager.git
cd skill-manager
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**Mac / Linux:**
```bash
git clone https://github.com/stbabaocha/skill-manager.git
cd skill-manager
bash setup.sh
```

**验证:**
```bash
python ~/.agents/skills/skill-manager/scripts/skill_manager.py list
```

> ⏱️ 等待 5-10 分钟，40 个科研 skill 自动安装完成。依赖缺失时脚本会自动提示 `[DEP_ACTION]`。

```bash
# 重新导出最新配置（含安装脚本）
python skill_manager.py export

# 把导出的文件夹分享给同学
```

---

## 📦 包含的 Skill 套件（40 个）

| 套件 | 数量 | 功能 |
|------|------|------|
| **Nature Skills** | 14 | 论文写作/润色/审稿/绘图/引用/回复/PPT/专利 |
| **PaperSpine** | 12 | 论文全流程写作/AIGC降重/LaTeX输出/审计 |
| **Academic Research** | 4 | 多agent论文流水线/审稿/深度调研 |
| **Grant Writer** | 4 | NSFC立项依据/文献综述/研究内容/技术路线 |
| **paper-craft** | 3 | 论文深度解析/图解/幻灯片 |
| **Google Code Review** | 1 | 仿真代码审查 |
| **Academic Poster** | 1 | 会议海报生成 |
| **skill-manager** | 1 | 管理器本身 |

---

## 🛠️ Manager 命令

```bash
python skill_manager.py list           # 列出所有已安装 skill
python skill_manager.py usage          # 调用速查表
python skill_manager.py info <名字>     # 查看 skill 详细说明书
python skill_manager.py agents <名字>   # 查看 skill 内部 Agent
python skill_manager.py doctor         # 健康诊断
python skill_manager.py compare <场景>  # 多角度交叉验证
python skill_manager.py advise <需求>   # 智能工作流推荐
python skill_manager.py wizard <类型>   # 项目向导 (paper/patent/grant)
python skill_manager.py export         # 导出安装包
python skill_manager.py search <关键词> # 搜索新 skill
python skill_manager.py install <repo> # 安装新 skill
python skill_manager.py update -y      # 一键更新所有 skill
python skill_manager.py remove <名字>   # 删除 skill
```

---

## 💬 支持的自然语言

安装后，在任何支持的 Agent 中直接说：

- "帮我审这篇稿子" → nature-reviewer + academic-paper-reviewer
- "帮我画 Nature 风格的图" → nature-figure
- "帮我写国自然立项依据" → fund-background-writer
- "帮我润色到 Nature 水准" → nature-polishing
- "帮我降 AIGC 率" → paper-spine-humanize
- "帮我做学术海报" → posterskill-academic-posters
- "审查我的 MATLAB 代码" → code-reviewer

---

## 📁 仓库结构

```
skill-manager/
├── SKILL.md              ← Agent Skill 定义
├── scripts/
│   └── skill_manager.py  ← 核心管理脚本
├── setup.ps1             ← Windows 一键安装（含依赖自动检测）
├── setup.sh              ← macOS/Linux 一键安装（含依赖自动检测）
├── install_all.ps1       ← Windows 批量安装（setup 自动调用）
└── README.md
```

---

## 🔄 更新

### 🤖 AI 一键更新
复制下面这段话发给任意 AI 助手：

> 请帮我更新 skill-manager 及所有 40 个科研 skill：
> 1. `cd ~/skill-manager-repo && git pull`（如不存在则 git clone）
> 2. 重新运行安装脚本：Windows 用 `powershell -ExecutionPolicy Bypass -File setup.ps1`，Mac/Linux 用 `bash setup.sh`
> 3. 运行 `python ~/.agents/skills/skill-manager/scripts/skill_manager.py update -y` 更新所有 skill

### 🖥️ 手动更新

```bash
# 更新管理器本身
git pull

# 更新所有已安装 skill
python skill_manager.py update -y

# 重新导出配置
python skill_manager.py export
```

---

## 📄 License

MIT
