---
name: skill-manager
description: |
  Unified skill manager for all AI agent platforms (GitHub Copilot, Claude Code, Cline,
  Codex, OpenClaw, Continue, Gemini CLI). Lists, removes, syncs, diagnoses, and deduplicates
  skills from any source (npx skills add, install.ps1, Claude Code plugins, Copilot agent-plugins,
  Cline skills-lock). Use when the user asks to manage, list, remove, clean up, or organize
  installed skills.
---

# Skill Manager v2.1 — 统一 Skill 管理 + 智能路由

管理跨越 GitHub Copilot、Claude Code/Cline、Codex、OpenClaw、Continue、Gemini CLI 的所有 skill。
**同时作为智能路由器，根据用户需求推荐最优 skill 组合工作流。**

## 发现源

| 路径 | 平台 |
|------|------|
| `~\.agents\skills\` | Copilot / Cline / Universal |
| `~\.claude\skills\` | Claude Code / Cline |
| `~\.cline\skills\` | Cline |
| `~\.codex\skills\` | Codex |
| `~\.openclaw\skills\` | OpenClaw |
| `~\.continue\skills\` | Continue |
| `~\.gemini\skills\` | Gemini CLI |
| `~\.claude\plugins\cache\*\*\skills\` | Claude Code 插件 |
| `~\.vscode\agent-plugins\**\skills\` | GitHub Copilot Agent-Plugins |
| Cline `skills-lock.json` | Cline (built-in) |

## 命令

运行 `python scripts/skill_manager.py <command>`。

### `list [--json] [--unique]`
列出所有平台的所有 skill，标注来源和安装方式。`--unique` 按名字去重并合并平台信息。

### `remove <name> [--from <platform>] [--yes]`
从指定平台（或全部平台）移除 skill。

### `sync --from <src> --to <dst> [--yes] [--force]`
将 skill 从一个平台同步到另一个。`--force` 覆盖已存在的。

### `where <name>`
查找某个 skill 安装在哪里（支持模糊匹配）。

### `info <name>`
查看 skill 详细信息，包括描述、调用方式、多平台副本情况。

### `usage`
快速参考表：所有常用 skill 的调用方式。

### `doctor`
健康诊断：检查所有平台目录、SKILL.md 完整性、重复检测、统计。

### `duplicates`
列出所有跨平台重复的 skill 及其路径。

## 智能路由（核心功能）

### 自动触发

当用户描述一个**复杂任务**时（而不仅是 skill 管理），自动运行 `recommend` 检索相关 skill 并推荐工作流：

| 用户说 | 路由结果 |
|--------|----------|
| "我想写一篇论文" / "帮我写 paper" | → 论文写作工作流 |
| "帮我审稿" / "模拟审稿" | → 审稿工作流 |
| "写一个基金" / "写 NSFC 申请" | → 基金写作工作流 |
| "帮我润色" / "polish 一下" | → 润色工作流 |
| "帮我找文献" / "文献检索" | → 文献检索工作流 |
| "做一个 PPT" / "论文汇报" | → PPT 生成工作流 |
| "帮我画图" / "论文配图" | → 科研绘图工作流 |
| "回复审稿意见" / "写 rebuttal" | → 审稿回复工作流 |
| "翻译这篇论文" / "精读论文" | → 论文阅读工作流 |
| "写专利" / "论文转专利" | → 专利写作工作流 |

### 路由流程

当检测到用户描述的是一个任务（而非 skill 管理请求）时：

1. 运行 `python scripts/skill_manager.py recommend "<用户需求>"`
2. 脚本匹配 skill 描述，返回相关 skill 列表和推荐工作流
3. **按顺序向用户展示推荐的 skill 组合**，格式如下：

```
📋 推荐工作流：论文写作

步骤 1️⃣ → nature-academic-search（文献检索）
   "帮我搜索 XX 领域的最新文献"

步骤 2️⃣ → nature-writing（论文撰写）
   "帮我写 Introduction 部分"

步骤 3️⃣ → nature-citation（添加引用）
   "给这段文字加上 Nature 系列引用"

步骤 4️⃣ → nature-polishing（润色）
   "帮我润色成 Nature 风格英文"

步骤 5️⃣ → nature-figure（配图）
   "帮我画 Figure 1"

步骤 6️⃣ → nature-reviewer（预审）
   "帮我模拟审稿人审一下"
```

4. 用户可以选择从任意步骤开始

### 预设工作流模板

#### 论文写作（从零到投稿）
1. `nature-academic-search` — 文献检索
2. `nature-citation` — 文献引用管理
3. `nature-writing` — 撰写各部分
4. `nature-figure` — 科研配图
5. `nature-polishing` — 英文润色
6. `nature-data` — 数据可用性声明
7. `nature-reviewer` — 预审（投稿前自检）
8. `nature-response` — 审稿回复（如需修回）

#### 基金申请（NSFC）
1. `fund-background-writer` — 立项依据/研究意义
2. `fund-literature-review-writer` — 国内外研究现状
3. `fund-research-content-writer` — 研究目标/内容/科学问题
4. `fund-technical-route-writer` — 研究方法/技术路线/创新特色

#### 论文阅读/汇报
1. `nature-reader` — 精读论文（中英对照）
2. `nature-paper2ppt` — 做汇报 PPT
3. `paper-analyzer` — 深度分析长文

#### 论文转专利
1. `nature-reader` — 读懂论文
2. `nature-paper-to-patent` — 转化为专利申请书

## Skill 管理命令

当用户说"管理 skill""列出 skill""删除 skill""清理 skill""诊断 skill"时：
1. 运行 `python scripts/skill_manager.py list --unique` 或对应命令
2. 格式化输出给用户
3. 根据用户选择执行 remove/sync/doctor
