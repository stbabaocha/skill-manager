---
name: skill-manager
description: |
  Unified skill manager for all AI agent platforms (GitHub Copilot, Claude Code, Cline,
  Codex, OpenClaw, Continue, Gemini CLI). Lists, removes, syncs, diagnoses, and deduplicates
  skills from any source (npx skills add, install.ps1, Claude Code plugins, Copilot agent-plugins,
  Cline skills-lock). Use when the user asks to manage, list, remove, clean up, or organize
  installed skills.
---

# Skill Manager v2.0 — 统一 Skill 管理

管理跨越 GitHub Copilot、Claude Code/Cline、Codex、OpenClaw、Continue、Gemini CLI 的所有 skill。

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

## 执行

当用户说"管理 skill""列出 skill""删除 skill""清理 skill""诊断 skill"时：
1. 运行 `python scripts/skill_manager.py list --unique` 或对应命令
2. 格式化输出给用户
3. 根据用户选择执行 remove/sync/doctor
