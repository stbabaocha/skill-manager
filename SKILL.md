---
name: skill-manager
description: |
  Unified skill manager for all AI agent platforms (GitHub Copilot, Claude Code, Cline,
  Codex, OpenClaw, Continue, Gemini CLI). Lists, removes, and syncs skills from any source
  (npx skills add, install.ps1, Claude Code plugins). Use when the user asks to manage,
  list, remove, clean up, or organize installed skills.
---

# Skill Manager — 统一 Skill 管理

管理跨越 GitHub Copilot、Claude Code/Cline、Codex、OpenClaw 的所有 skill。

## 发现源

| 路径 | 平台 |
|------|------|
| `~\.agents\skills\` | Copilot / Cline / Universal |
| `~\.claude\skills\` | Claude Code / Cline |
| `~\.codex\skills\` | Codex |
| `~\.openclaw\skills\` | OpenClaw |
| `~\.claude\plugins\cache\*\*\skills\` | Claude Code 插件 |
| `~\.continue\skills\` | Continue |
| `~\.gemini\skills\` | Gemini CLI |

## 命令

运行 `python scripts/skill_manager.py <command>` 或 `pwsh scripts/skill_manager.ps1 <command>`。

### `list [--json]`
列出所有平台的所有 skill，标注来源和安装方式。

### `remove <name> [--from <platform>]`
从指定平台（或全部平台）移除 skill。

### `sync --from <src> --to <dst>`
将 skill 从一个平台同步到另一个。

### `where <name>`
查找某个 skill 安装在哪里。

## 执行

当用户说"管理 skill""列出 skill""删除 skill""清理 skill"时：
1. 运行 `python scripts/skill_manager.py list --json`
2. 格式化输出给用户
3. 根据用户选择执行 remove/sync
