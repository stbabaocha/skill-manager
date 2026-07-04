# Skill Manager — 科研 Agent Skill 统一管理器

[![Skills](https://img.shields.io/badge/skills-40-blue)](https://github.com/stbabaocha/skill-manager)
[![Platforms](https://img.shields.io/badge/platforms-7-green)](https://github.com/stbabaocha/skill-manager)
[![Python](https://img.shields.io/badge/python-≥3.9-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**一键安装 · 统一管理 · 智能工作流推荐 · 支持 7 个 AI 平台**

管理 GitHub Copilot、Claude Code、Cline、Codex 等平台上 **40 个科研 Agent Skill** 的命令行工具。

---

## 🚀 快速开始

### 🤖 AI 一键安装（推荐 · 零基础可用）

**把下面这段话复制粘贴到任意 AI 编程助手**（Copilot / Claude Code / Cline / Codex 均可），AI 会自动完成一切——包括安装缺失的依赖：

---

> 请帮我安装 skill-manager（40 个科研 AI Skill 的统一管理器）：
>
> 1. 克隆仓库：`git clone https://github.com/stbabaocha/skill-manager.git`，如果已存在则 `git pull`
> 2. 进入目录并运行安装脚本：
>    - **Windows**：`powershell -ExecutionPolicy Bypass -File setup.ps1`
>    - **macOS / Linux**：`bash setup.sh`
> 3. 脚本会自动检测并安装缺失的依赖（Git/Node.js/Python），Mac 会自动安装 Homebrew
> 4. 安装完成后运行验证：`python ~/.agents/skills/skill-manager/scripts/skill_manager.py list --unique`

---

> 💡 **上面这段是写给你的 AI 助手看的，直接发过去即可。** 全程自动，无需手动操作。

### 🖥️ 手动安装

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
python ~/.agents/skills/skill-manager/scripts/skill_manager.py list --unique
```

> ⏱️ 首次安装约 5-10 分钟。脚本会自动安装缺失依赖（Homebrew / Git / Node.js / Python）。

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

## 🛠️ 命令

```bash
# 基础管理
python skill_manager.py list [--unique]   # 列出所有已安装 skill（--unique 去重）
python skill_manager.py list --json       # JSON 格式输出
python skill_manager.py where <名字>      # 查找 skill 安装位置
python skill_manager.py info <名字>       # 查看 skill 详细信息
python skill_manager.py usage             # 调用方式速查表
python skill_manager.py doctor            # 健康诊断
python skill_manager.py duplicates        # 列出跨平台重复

# 智能推荐 ⭐
python skill_manager.py recommend <需求>  # 根据你的需求推荐 skill 工作流

# 跨平台操作
python skill_manager.py sync --from agents --to claude [-y] [--force]  # 同步
python skill_manager.py sync-all [-y] [--force]   # 一键同步到所有平台
python skill_manager.py remove <名字> [-y]         # 删除 skill
```

### 智能推荐示例

```bash
python skill_manager.py recommend 我想写一篇论文
# → 推荐：文献检索 → 撰写 → 配图 → 润色 → 预审 完整工作流

python skill_manager.py recommend 写基金
# → 推荐：立项依据 → 文献综述 → 研究内容 → 技术路线

python skill_manager.py recommend 帮我模拟审稿
# → 推荐：nature-reviewer（模拟 3 位审稿人）
```

---

## 💬 自然语言触发

安装后，在任何支持的 AI Agent 中直接说中文：

| 你说 | 触发的 Skill |
|------|-------------|
| "帮我审这篇稿子" | nature-reviewer |
| "帮我画 Nature 风格的图" | nature-figure |
| "帮我写国自然立项依据" | fund-background-writer |
| "帮我润色到 Nature 水准" | nature-polishing |
| "帮我降 AIGC 率" | paper-spine-humanize |
| "帮我做学术海报" | posterskill-academic-posters |
| "审查我的代码" | code-reviewer |
| "帮我写论文" | nature-writing |
| "帮我做论文PPT" | nature-paper2ppt |
| "帮我把论文转成专利" | nature-paper-to-patent |

---

## 📁 仓库结构

```
skill-manager/
├── SKILL.md              ← Agent Skill 定义（AI 直接读取）
├── scripts/
│   └── skill_manager.py  ← 核心管理脚本 (v2.1)
├── setup.ps1             ← Windows 安装（含自动依赖安装）
├── setup.sh              ← macOS/Linux 安装（含 Homebrew 自动安装）
├── install_all.ps1       ← Windows 批量安装 40 个 skill
├── install_all.sh        ← macOS/Linux 批量安装 40 个 skill
├── pyproject.toml        ← Python 项目配置
├── cover.html            ← 封面页
├── LICENSE               ← MIT 许可证
└── README.md
```

---

## 🔄 更新

### 🤖 AI 一键更新

复制下面这段话发给任意 AI 助手：

> 请帮我更新 skill-manager：
> 1. `cd skill-manager && git pull`（如不存在则 `git clone https://github.com/stbabaocha/skill-manager.git`）
> 2. 重新运行安装脚本：Windows 用 `powershell -ExecutionPolicy Bypass -File setup.ps1`，Mac/Linux 用 `bash setup.sh`

### 🖥️ 手动更新

```bash
cd skill-manager
git pull
# Windows
powershell -ExecutionPolicy Bypass -File setup.ps1
# Mac/Linux
bash setup.sh
```

---

## ❌ 卸载

```bash
# 删除所有已安装的 skill
rm -rf ~/.agents/skills ~/.claude/skills ~/.codex/skills ~/.continue/skills

# 删除仓库
rm -rf skill-manager
```

Windows:
```powershell
Remove-Item -Recurse -Force $env:USERPROFILE\.agents\skills, $env:USERPROFILE\.claude\skills
```

---

## 🤝 贡献

欢迎提 Issue 和 PR！如果你有好用的科研 AI skill，也可以提交给我们集成进来。

---

## 📄 License

[MIT](LICENSE)
