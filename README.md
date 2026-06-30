# Skill Manager — 科研 Agent Skill 统一管理器

[![Skills](https://img.shields.io/badge/skills-40-blue)](https://github.com)
[![Platforms](https://img.shields.io/badge/platforms-7-green)]()

**一键安装 · 统一管理 · 多角度交叉验证 · 智能工作流推荐**

管理 GitHub Copilot、Claude Code、Cline、Codex 等平台上 **40 个科研 Agent Skill** 的命令行工具。

---

## 🚀 快速开始

### 同学/用户（只需 3 步）

```powershell
# 1. 下载本仓库
git clone https://github.com/stbabaocha/skill-manager.git
cd skill-manager

# 2. 运行安装
powershell -ExecutionPolicy Bypass -File setup.ps1

# 3. 验证
python ~\.agents\skills\skill-manager\scripts\skill_manager.py list
```

> 等待 5-10 分钟，40 个科研 skill 自动安装完成。

### 已有 manager 的用户（更新配置）

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
├── setup.ps1             ← 一键安装入口
├── install_all.ps1       ← 批量安装（setup.ps1 自动调用）
└── README.md
```

---

## 🔄 更新

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
