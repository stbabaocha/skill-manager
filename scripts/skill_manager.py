#!/usr/bin/env python3
"""
Skill Manager v2.0 — 统一管理所有平台的 Agent Skills

用法:
    python skill_manager.py list [--json] [--unique]
    python skill_manager.py remove <name> [--from <platform>] [--yes]
    python skill_manager.py where <name>
    python skill_manager.py sync --from <src> --to <dst> [--yes] [--force]
    python skill_manager.py info <name>
    python skill_manager.py usage
    python skill_manager.py doctor
    python skill_manager.py duplicates
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

HOME = Path.home()

# ── 所有已知的 skill 发现路径 ─────────────────────────────────────
SKILL_ROOTS = {
    "agents": {
        "path": HOME / ".agents" / "skills",
        "platforms": ["GitHub Copilot", "Cline", "Universal"],
        "install_method": "npx skills add / universal",
    },
    "claude": {
        "path": HOME / ".claude" / "skills",
        "platforms": ["Claude Code", "Cline"],
        "install_method": "install.ps1 / manual",
    },
    "cline": {
        "path": HOME / ".cline" / "skills",
        "platforms": ["Cline"],
        "install_method": "manual",
    },
    "codex": {
        "path": HOME / ".codex" / "skills",
        "platforms": ["Codex"],
        "install_method": "install.ps1 / manual",
    },
    "openclaw": {
        "path": HOME / ".openclaw" / "skills",
        "platforms": ["OpenClaw"],
        "install_method": "install.ps1 / manual",
    },
    "continue": {
        "path": HOME / ".continue" / "skills",
        "platforms": ["Continue"],
        "install_method": "manual",
    },
    "gemini": {
        "path": HOME / ".gemini" / "skills",
        "platforms": ["Gemini CLI"],
        "install_method": "manual",
    },
}

# Claude Code 插件目录
CLAUDE_PLUGINS_ROOT = HOME / ".claude" / "plugins" / "cache"

# GitHub Copilot agent-plugins 目录
COPILOT_AGENT_PLUGINS = HOME / ".vscode" / "agent-plugins"

# Cline skills-lock.json
CLINE_SKILLS_LOCK = HOME / ".vscode" / "extensions"


def _safe_read(path: Path, max_bytes: int = 50000) -> str:
    """安全读取文件，处理编码问题"""
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")[:max_bytes]
        except Exception:
            continue
    return ""


def _read_skill_description(skill_path_str: str) -> str:
    """从 SKILL.md 读取 description（修复多行 YAML 解析）"""
    skill_md = Path(skill_path_str) / "SKILL.md"
    if not skill_md.exists():
        return ""
    try:
        text = _safe_read(skill_md)
        if not text.startswith("---"):
            return ""
        end = text.find("---", 3)
        if end <= 0:
            return ""
        fm = text[3:end].strip()
        lines = fm.split("\n")
        desc_lines = []
        in_desc = False
        for i, line in enumerate(lines):
            if line.startswith("description:"):
                rest = line.split(":", 1)[1].strip()
                if rest and rest != "|" and rest != ">":
                    # 单行描述
                    return rest[:300]
                # 多行描述（| 或 >）
                in_desc = True
                continue
            if in_desc:
                if line and not line[0].isspace():
                    # 新的顶级 key，结束
                    break
                desc_lines.append(line.strip())
        return " ".join(desc_lines)[:300] if desc_lines else ""
    except Exception:
        return ""


def _find_cline_lock_skills() -> list:
    """扫描 Cline 扩展的 skills-lock.json"""
    skills = []
    if not CLINE_SKILLS_LOCK.exists():
        return skills

    for ext_dir in CLINE_SKILLS_LOCK.iterdir():
        if not ext_dir.is_dir():
            continue
        if "claude-dev" not in ext_dir.name and "cline" not in ext_dir.name.lower():
            continue
        lock_file = ext_dir / "skills-lock.json"
        if not lock_file.exists():
            continue
        try:
            data = json.loads(_safe_read(lock_file))
            for name, info in data.get("skills", {}).items():
                skill_path = ext_dir / info.get("skillPath", "")
                skills.append({
                    "name": name,
                    "root": "cline-lock",
                    "path": str(skill_path.parent if skill_path.exists() else ext_dir),
                    "platforms": ["Cline (built-in)"],
                    "install_method": f"Cline SDK: {info.get('source', 'unknown')}",
                    "has_skill_md": skill_path.exists(),
                    "source_type": info.get("sourceType", "unknown"),
                })
        except Exception:
            continue
    return skills


def _find_copilot_agent_skills() -> list:
    """扫描 .vscode/agent-plugins/ 下的 Copilot skills"""
    skills = []
    if not COPILOT_AGENT_PLUGINS.exists():
        return skills

    # 遍历 org/repo/skills/ 结构
    for org_dir in COPILOT_AGENT_PLUGINS.iterdir():
        if not org_dir.is_dir():
            continue
        for owner_dir in org_dir.iterdir():
            if not owner_dir.is_dir():
                continue
            for repo_dir in owner_dir.iterdir():
                if not repo_dir.is_dir():
                    continue
                # 检查 skills/ 子目录
                skills_dir = repo_dir / "skills"
                if not skills_dir.exists():
                    # 也检查 plugins/*/skills/
                    for plugin_dir in repo_dir.glob("plugins/*/skills"):
                        if plugin_dir.exists():
                            for item in sorted(plugin_dir.iterdir()):
                                if item.is_dir() and not item.name.startswith("."):
                                    skill_md = item / "SKILL.md"
                                    plugin_name = item.parent.parent.name
                                    skills.append({
                                        "name": item.name,
                                        "root": f"copilot-plugin/{owner_dir.name}/{repo_dir.name}/{plugin_name}",
                                        "path": str(item),
                                        "platforms": ["GitHub Copilot (plugin)"],
                                        "install_method": f"Copilot plugin: {repo_dir.name}/{plugin_name}",
                                        "has_skill_md": skill_md.exists(),
                                    })
                    continue

                for item in sorted(skills_dir.iterdir()):
                    if item.is_dir() and not item.name.startswith("."):
                        skill_md = item / "SKILL.md"
                        skills.append({
                            "name": item.name,
                            "root": f"copilot/{owner_dir.name}/{repo_dir.name}",
                            "path": str(item),
                            "platforms": ["GitHub Copilot (agent-plugin)"],
                            "install_method": f"Copilot agent-plugin: {owner_dir.name}/{repo_dir.name}",
                            "has_skill_md": skill_md.exists(),
                        })
    return skills


def discover_all_skills() -> list[dict]:
    """发现所有 skill（全源扫描）"""
    skills = []
    seen = set()

    # 1. 标准 skill 目录（agents/claude/cline/codex/openclaw/continue/gemini）
    for key, cfg in SKILL_ROOTS.items():
        skill_dir = cfg["path"]
        if not skill_dir.exists():
            continue
        for item in sorted(skill_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                skill_md = item / "SKILL.md"
                if skill_md.exists() or any(item.glob("*.md")):
                    uid = f"{key}:{item.name}"
                    if uid in seen:
                        continue
                    seen.add(uid)
                    skills.append({
                        "name": item.name,
                        "root": key,
                        "path": str(item),
                        "platforms": cfg["platforms"],
                        "install_method": cfg["install_method"],
                        "has_skill_md": skill_md.exists(),
                    })

    # 2. Claude Code 插件 skills
    if CLAUDE_PLUGINS_ROOT.exists():
        for org_dir in CLAUDE_PLUGINS_ROOT.iterdir():
            if not org_dir.is_dir():
                continue
            for plugin_dir in org_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                for ver_dir in sorted(plugin_dir.iterdir(), reverse=True):
                    skills_dir = ver_dir / "skills"
                    if not skills_dir.exists():
                        continue
                    for item in skills_dir.iterdir():
                        if item.is_dir():
                            skill_md = item / "SKILL.md"
                            name = item.name
                            has_md = skill_md.exists()
                        else:
                            continue

                        uid = f"plugin:{plugin_dir.name}:{name}"
                        if uid in seen:
                            continue
                        seen.add(uid)
                        skills.append({
                            "name": name,
                            "root": f"plugin/{plugin_dir.name}",
                            "path": str(item),
                            "platforms": ["Claude Code (plugin)"],
                            "install_method": f"Claude Code plugin: {plugin_dir.name}",
                            "has_skill_md": has_md,
                        })
                    break  # 只看最新版本

    # 3. GitHub Copilot agent-plugins
    copilot_skills = _find_copilot_agent_skills()
    for s in copilot_skills:
        uid = f"copilot:{s['name']}:{s['root']}"
        if uid not in seen:
            seen.add(uid)
            skills.append(s)

    # 4. Cline skills-lock.json
    cline_skills = _find_cline_lock_skills()
    for s in cline_skills:
        uid = f"cline-lock:{s['name']}"
        if uid not in seen:
            seen.add(uid)
            skills.append(s)

    return skills


def _get_unique_skills(skills: list) -> dict:
    """按名字去重，合并平台信息"""
    by_name = defaultdict(lambda: {"platforms": set(), "roots": [], "paths": []})
    for s in skills:
        entry = by_name[s["name"]]
        for p in s["platforms"]:
            entry["platforms"].add(p)
        entry["roots"].append(s["root"])
        entry["paths"].append(s["path"])
        entry["has_skill_md"] = entry.get("has_skill_md", False) or s["has_skill_md"]
        entry["install_method"] = s["install_method"]
    return by_name


def cmd_list(json_output: bool = False, unique: bool = False):
    """列出所有 skill"""
    skills = discover_all_skills()

    if json_output:
        if unique:
            by_name = _get_unique_skills(skills)
            result = []
            for name, info in sorted(by_name.items()):
                result.append({
                    "name": name,
                    "platforms": sorted(info["platforms"]),
                    "roots": info["roots"],
                    "has_skill_md": info["has_skill_md"],
                    "copies": len(info["paths"]),
                })
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(skills, ensure_ascii=False, indent=2))
        return

    if not skills:
        print("No skills found.")
        return

    if unique:
        by_name = _get_unique_skills(skills)
        print(f"\n{'='*70}")
        print(f"  Skill Manager v2.0 — 共发现 {len(by_name)} 个独立 Skill（{len(skills)} 份副本）")
        print(f"{'='*70}")

        # 按类别分组
        categories = defaultdict(list)
        for name, info in sorted(by_name.items()):
            if "Copilot (agent-plugin)" in str(info["platforms"]):
                categories["GitHub Copilot Agent-Plugins"].append((name, info))
            elif "Copilot (plugin)" in str(info["platforms"]):
                categories["GitHub Copilot Plugins"].append((name, info))
            elif "Claude Code (plugin)" in str(info["platforms"]):
                categories["Claude Code Plugins"].append((name, info))
            else:
                categories["自安装 Skills"].append((name, info))

        for cat, items in categories.items():
            print(f"\n📂 {cat}  ({len(items)} 个)")
            print(f"   {'─'*55}")
            for name, info in items:
                status = "✅" if info["has_skill_md"] else "⚠️"
                plats = ", ".join(sorted(info["platforms"]))
                copies = f" ×{len(info['paths'])}" if len(info["paths"]) > 1 else ""
                print(f"   {status} {name:<40} [{plats}]{copies}")
        print()
        return

    # 按来源分组
    by_root = defaultdict(list)
    for s in skills:
        by_root[s["root"]].append(s)

    print(f"\n{'='*70}")
    print(f"  Skill Manager v2.0 — 共发现 {len(skills)} 份 Skill 记录")
    print(f"{'='*70}")

    for root, group in sorted(by_root.items()):
        platform_str = ", ".join(group[0]["platforms"]) if group else root
        method = group[0]["install_method"]
        print(f"\n📂 {root}  ({platform_str}) — {method}  [{len(group)} 个]")
        print(f"   {'─'*55}")
        for s in group:
            status = "✅" if s["has_skill_md"] else "⚠️"
            print(f"   {status} {s['name']}")
    print()


def cmd_where(name: str):
    """查找 skill 位置"""
    skills = discover_all_skills()
    matches = [s for s in skills if s["name"].lower() == name.lower()]

    if not matches:
        matches = [s for s in skills if name.lower() in s["name"].lower()]

    if not matches:
        print(f"Skill not found: {name}")
        print(f"提示: 试试  python skill_manager.py list --unique  查看所有 skill")
        return

    print(f"\n找到 {len(matches)} 份匹配:")
    for s in matches:
        print(f"\n  📦 {s['name']}")
        print(f"     路径: {s['path']}")
        print(f"     平台: {', '.join(s['platforms'])}")
        print(f"     来源: {s['root']}")
        print(f"     安装方式: {s['install_method']}")
        print(f"     SKILL.md: {'✅' if s['has_skill_md'] else '❌ 缺失'}")


def cmd_remove(name: str, from_root: str = None, yes: bool = False):
    """移除 skill"""
    skills = discover_all_skills()
    matches = [s for s in skills if s["name"] == name]

    if from_root:
        matches = [s for s in matches if s["root"] == from_root]

    if not matches:
        print(f"Skill not found: {name}")
        return

    for s in matches:
        target = Path(s["path"])
        if not target.exists():
            print(f"Already removed: {s['name']} from {s['root']}")
            continue

        if not yes:
            resp = input(f"Remove {s['name']} from {s['root']} ({', '.join(s['platforms'])})? [y/N] ")
            if resp.lower() != "y":
                continue

        if target.is_dir():
            shutil.rmtree(target)
            print(f"✅ Removed: {s['name']} ({s['root']})")
        elif target.is_file():
            target.unlink()
            print(f"✅ Removed: {s['name']} ({s['root']}) [file]")


def cmd_sync(src_root: str, dst_root: str, yes: bool = False, force: bool = False):
    """同步 skill 从一个平台到另一个"""
    if src_root not in SKILL_ROOTS or dst_root not in SKILL_ROOTS:
        print(f"Unknown root. Available: {', '.join(SKILL_ROOTS.keys())}")
        return

    src_dir = SKILL_ROOTS[src_root]["path"]
    dst_dir = SKILL_ROOTS[dst_root]["path"]

    if not src_dir.exists():
        print(f"Source not found: {src_dir}")
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    synced = 0
    skipped = 0
    for item in sorted(src_dir.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        dst_item = dst_dir / item.name
        if dst_item.exists() and not force:
            skipped += 1
            continue
        if not yes:
            action = "Overwrite" if dst_item.exists() else "Copy"
            resp = input(f"{action} {item.name} → {dst_root}? [y/N] ")
            if resp.lower() != "y":
                continue
        if dst_item.exists():
            shutil.rmtree(dst_item)
        shutil.copytree(item, dst_item)
        print(f"✅ Synced: {item.name} → {dst_root}")
        synced += 1

    if synced == 0 and skipped > 0:
        print(f"Nothing new to sync ({skipped} already exist). Use --force to overwrite.")
    elif synced == 0:
        print("Nothing to sync.")
    else:
        print(f"\n同步完成: {synced} 个 skill")


def cmd_info(name: str):
    """查看 skill 详细信息"""
    skills = discover_all_skills()
    matches = [s for s in skills if s["name"].lower() == name.lower()]

    if not matches:
        matches = [s for s in skills if name.lower() in s["name"].lower()]

    if not matches:
        print(f"Skill not found: {name}")
        return

    # 去重 - 只展示一个详细版本
    shown = set()
    for s in matches:
        if s["name"] in shown:
            continue
        shown.add(s["name"])

        desc = _read_skill_description(s["path"])
        usage = SKILL_USAGE.get(s["name"], {})

        print(f"\n{'='*60}")
        print(f"  📦 {s['name']}")
        print(f"{'='*60}")
        if desc:
            print(f"  描述: {desc}")
        print(f"  安装位置: {s['path']}")
        print(f"  可用平台: {', '.join(s['platforms'])}")
        print(f"  安装方式: {s['install_method']}")

        # 查找同名的其他副本
        copies = [x for x in skills if x["name"] == s["name"] and x["root"] != s["root"]]
        if copies:
            print(f"  其他副本: {len(copies)} 个 ({', '.join(c['root'] for c in copies)})")

        if usage:
            print(f"\n  📝 如何调用:")
            print(f"     {usage.get('how', '自然语言触发')}")
            print(f"  💡 示例:")
            print(f"     {usage.get('example', '无')}")
            if usage.get("note"):
                print(f"  ℹ️  备注: {usage['note']}")
        else:
            print(f"\n  📝 调用方式: 自然语言触发（无特定命令）")
    print()


def cmd_usage():
    """快速参考表"""
    print(f"\n{'='*75}")
    print(f"  Skill 调用速查表")
    print(f"{'='*75}")
    print(f"  {'Skill':<30} {'调用方式':<44}")
    print(f"  {'─'*30} {'─'*44}")

    for name, info in sorted(SKILL_USAGE.items()):
        how = info["how"]
        if len(how) > 42:
            how = how[:40] + "…"
        print(f"  {name:<30} {how:<44}")

    print(f"\n  💡 提示：绝大部分 paper-spine-* 子 skill 由 /paperspine 自动调用")
    print(f"  💡 academic-* 系列由关键词触发，直接描述需求即可")
    print(f"  💡 Copilot agent-plugin skills 需在 VS Code Copilot Chat 中使用")
    print()


def cmd_doctor():
    """健康诊断"""
    print(f"\n{'='*60}")
    print(f"  🩺 Skill Manager — 健康诊断")
    print(f"{'='*60}\n")

    skills = discover_all_skills()
    issues = []
    warnings = []

    # 1. 检查各平台目录
    print("📂 平台目录检查:")
    for key, cfg in SKILL_ROOTS.items():
        path = cfg["path"]
        exists = path.exists()
        count = len([d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")]) if exists else 0
        status = "✅" if exists and count > 0 else ("⚠️" if exists else "❌")
        print(f"   {status} {key:<12} {str(path):<50} [{count} skills]")
        if not exists:
            warnings.append(f"{key} 目录不存在: {path}")

    # Copilot agent-plugins
    copilot_count = len([s for s in skills if "copilot" in s["root"].lower()])
    print(f"   {'✅' if copilot_count > 0 else '⚠️'} {'copilot':<12} {str(COPILOT_AGENT_PLUGINS):<50} [{copilot_count} skills]")

    # Claude plugins
    plugin_count = len([s for s in skills if "plugin/" in s["root"]])
    print(f"   {'✅' if plugin_count > 0 else '⚠️'} {'plugins':<12} {str(CLAUDE_PLUGINS_ROOT):<50} [{plugin_count} skills]")

    # Cline lock
    cline_lock_count = len([s for s in skills if s["root"] == "cline-lock"])
    print(f"   {'✅' if cline_lock_count > 0 else 'ℹ️'} {'cline-lock':<12} skills-lock.json{'':<34} [{cline_lock_count} skills]")

    # 2. SKILL.md 检查
    print(f"\n📄 SKILL.md 完整性:")
    no_md = [s for s in skills if not s["has_skill_md"]]
    if no_md:
        for s in no_md:
            print(f"   ⚠️ 缺少 SKILL.md: {s['name']} ({s['root']})")
            issues.append(f"{s['name']} 缺少 SKILL.md")
    else:
        print(f"   ✅ 所有 skill 都有 SKILL.md")

    # 3. 重复检测
    print(f"\n🔄 重复检测:")
    by_name = _get_unique_skills(skills)
    dups = {name: info for name, info in by_name.items() if len(info["paths"]) > 1}
    if dups:
        # 只报告标准目录中的重复（copilot 的天然有复本）
        real_dups = {}
        for name, info in dups.items():
            std_roots = [r for r in info["roots"] if not r.startswith("copilot")]
            if len(std_roots) > 1:
                real_dups[name] = info
        if real_dups:
            print(f"   ⚠️ {len(real_dups)} 个 skill 在多个标准平台有副本:")
            for name, info in sorted(real_dups.items()):
                std_roots = [r for r in info["roots"] if not r.startswith("copilot")]
                print(f"      {name}: {', '.join(std_roots)}")
            warnings.append(f"{len(real_dups)} 个 skill 有跨平台重复")
        else:
            print(f"   ✅ 标准平台无不必要重复")
    else:
        print(f"   ✅ 无重复")

    # 4. 统计
    unique_count = len(by_name)
    print(f"\n📊 统计:")
    print(f"   总记录数: {len(skills)}")
    print(f"   独立 skill 数: {unique_count}")
    print(f"   覆盖平台: {len([k for k, v in SKILL_ROOTS.items() if v['path'].exists()])}/{len(SKILL_ROOTS)}")

    # 5. 总结
    print(f"\n{'─'*60}")
    if issues:
        print(f"  ❌ 发现 {len(issues)} 个问题:")
        for i in issues:
            print(f"     • {i}")
    if warnings:
        print(f"  ⚠️ {len(warnings)} 个警告:")
        for w in warnings:
            print(f"     • {w}")
    if not issues and not warnings:
        print(f"  ✅ 一切正常!")
    print()


def cmd_duplicates():
    """列出所有跨平台重复的 skill"""
    skills = discover_all_skills()
    by_name = _get_unique_skills(skills)

    dups = {name: info for name, info in by_name.items() if len(info["paths"]) > 1}

    if not dups:
        print("No duplicates found.")
        return

    print(f"\n{'='*70}")
    print(f"  跨平台重复 Skill ({len(dups)} 个)")
    print(f"{'='*70}")

    for name, info in sorted(dups.items()):
        print(f"\n  📦 {name}  ({len(info['paths'])} 份)")
        for root, path in zip(info["roots"], info["paths"]):
            print(f"     • [{root}] {path}")
    print()


# ── 已知的 skill 调用方式 ──────────────────────────────────────────

SKILL_USAGE = {
    "paper-analyzer": {
        "how": "/paper-analyzer <arxiv-url|pdf路径|粘贴文本>",
        "example": '/paper-analyzer https://arxiv.org/abs/1706.03762',
        "platforms": "Copilot / Cline",
        "note": "也支持自然语言：\"帮我分析这篇论文\"",
    },
    "paper-comic": {
        "how": "/paper-comic <pdf|arxiv-url> [--style sketchnote|paper-figure]",
        "example": "/paper-comic paper.pdf --style sketchnote",
        "platforms": "Copilot / Cline",
        "note": "先生成方案让你确认，确认后才出图",
    },
    "paper-deck": {
        "how": "/paper-deck <pdf|arxiv-url> [--style journal-minimal] [--slides 12]",
        "example": "/paper-deck https://arxiv.org/abs/1706.03762 --slides 12",
        "platforms": "Copilot / Cline",
        "note": "也支持：\"论文PPT\"\"把论文做成幻灯片\"",
    },
    "paper-spine": {
        "how": "/paperspine",
        "example": "/paperspine",
        "platforms": "Claude Code / Cline",
        "note": "主控 skill，自动路由到配置→调研→引用→写作→LaTeX→审计",
    },
    "paper-spine-humanize": {
        "how": "自动调用（paper-spine 内部步骤 #8）",
        "example": '设置 humanize_tier 为 light/medium/heavy',
        "platforms": "Claude Code / Cline",
        "note": "降 AIGC 检测率",
    },
    "nature-polishing": {
        "how": "\"帮我润色到 Nature 水准\" / \"polish my manuscript\"",
        "example": "粘贴段落后说\"润色\"",
        "platforms": "Cline / Claude Code",
        "note": "学术英语润色",
    },
    "nature-figure": {
        "how": "\"帮我画 Nature 风格的图\"",
        "example": "描述数据和图形需求",
        "platforms": "Cline / Claude Code",
        "note": "支持 Python matplotlib 和 R ggplot2",
    },
    "nature-reviewer": {
        "how": "\"帮我审这篇稿子\" / \"模拟审稿\"",
        "example": "提供论文后请求审稿",
        "platforms": "Cline / Claude Code",
        "note": "模拟 3 位审稿人 + 交叉评审",
    },
    "nature-writing": {
        "how": "\"帮我写论文\" / \"draft introduction\"",
        "example": "提供研究结果和 claim 后请求写作",
        "platforms": "Cline / Claude Code",
        "note": "Nature 风格论文写作",
    },
    "fund-background-writer": {
        "how": "\"帮我写国自然立项依据\"",
        "example": "提供研究方向后请求",
        "platforms": "Cline / Claude Code",
        "note": "NSFC 立项依据/研究意义",
    },
    "academic-paper": {
        "how": "\"write paper\" / \"academic paper\" / \"写论文\"",
        "example": "启动后按模式选 10 modes",
        "platforms": "Claude Code (插件)",
        "note": "12-agent 论文写作流水线",
    },
    "deep-research": {
        "how": "\"deep research\" / \"文献综述\" / \"系统综述\"",
        "example": "启动后选 7 种模式之一",
        "platforms": "Claude Code (插件)",
        "note": "13-agent 深度研究流水线",
    },
    "skill-manager": {
        "how": "\"管理 skill\" / \"列出所有 skill\" / \"删除 xx skill\"",
        "example": "python skill_manager.py list --unique",
        "platforms": "所有平台",
        "note": "本工具",
    },
}


# ── 智能路由/推荐 ──────────────────────────────────────────────

# 预设工作流模板
WORKFLOW_TEMPLATES = {
    "论文写作": {
        "keywords": ["写论文", "论文", "写 paper", "写manuscript", "撰写论文", "write paper", "draft paper", "写稿", "paper", "manuscript"],
        "steps": [
            ("nature-academic-search", "文献检索", "帮我搜索 XX 领域的最新文献"),
            ("nature-citation", "文献引用管理", "给这段文字加上引用"),
            ("nature-writing", "撰写各部分", "帮我写 Introduction/Methods/Results"),
            ("nature-figure", "科研配图", "帮我画 Figure 1"),
            ("nature-polishing", "英文润色", "帮我润色成 Nature 风格英文"),
            ("nature-data", "数据可用性声明", "帮我写 Data Availability"),
            ("nature-reviewer", "预审（投稿前自检）", "帮我模拟审稿人审一下"),
            ("nature-response", "审稿回复", "帮我回复审稿意见"),
        ],
    },
    "基金申请": {
        "keywords": ["写基金", "NSFC", "国自然", "基金申请", "立项依据", "fund", "grant"],
        "steps": [
            ("fund-background-writer", "立项依据/研究意义", "帮我写立项依据"),
            ("fund-literature-review-writer", "国内外研究现状", "帮我写文献综述部分"),
            ("fund-research-content-writer", "研究目标/内容/科学问题", "帮我拆解研究内容"),
            ("fund-technical-route-writer", "研究方法/技术路线/创新特色", "帮我写技术路线"),
        ],
    },
    "论文阅读": {
        "keywords": ["读论文", "精读", "翻译论文", "论文翻译", "read paper", "paper reading", "文献阅读"],
        "steps": [
            ("nature-reader", "精读论文（中英对照）", "帮我精读这篇论文"),
            ("paper-analyzer", "深度分析长文", "帮我深度分析这篇论文"),
            ("nature-paper2ppt", "做汇报 PPT", "帮我把这篇论文做成 PPT"),
        ],
    },
    "论文汇报": {
        "keywords": ["做PPT", "论文汇报", "组会", "学术汇报", "paper presentation", "做幻灯片", "slides"],
        "steps": [
            ("nature-reader", "先精读论文", "帮我读懂这篇论文"),
            ("nature-paper2ppt", "生成 PPT", "帮我做一个组会汇报 PPT"),
        ],
    },
    "审稿模拟": {
        "keywords": ["审稿", "模拟审稿", "reviewer", "peer review", "预审", "自审"],
        "steps": [
            ("nature-reviewer", "模拟审稿人评估", "帮我模拟审稿"),
        ],
    },
    "审稿回复": {
        "keywords": ["回复审稿", "rebuttal", "revision", "修回", "审稿意见", "response to reviewer"],
        "steps": [
            ("nature-response", "逐点回复审稿意见", "帮我回复审稿意见"),
        ],
    },
    "润色": {
        "keywords": ["润色", "polish", "改写", "语言润色", "英文润色", "proofreading"],
        "steps": [
            ("nature-polishing", "学术英文润色", "帮我润色这段文字"),
        ],
    },
    "文献检索": {
        "keywords": ["找文献", "搜文献", "文献检索", "literature search", "查文献", "找论文"],
        "steps": [
            ("nature-academic-search", "多源文献检索", "帮我搜索关于 XX 的文献"),
            ("nature-citation", "引用管理", "帮我整理引用"),
            ("nature-literature-pipeline", "自动文献发现", "帮我建立文献自动追踪"),
        ],
    },
    "科研配图": {
        "keywords": ["画图", "绘图", "配图", "figure", "plot", "可视化", "作图"],
        "steps": [
            ("nature-figure", "期刊级科研配图", "帮我画一个 XX 图"),
            ("paper-comic", "论文方法图解", "帮我用图解说明方法"),
        ],
    },
    "论文转专利": {
        "keywords": ["写专利", "转专利", "patent", "专利申请"],
        "steps": [
            ("nature-reader", "读懂论文", "帮我读懂这篇论文的方法"),
            ("nature-paper-to-patent", "转化为专利", "帮我把论文转成专利申请书"),
        ],
    },
    "代码审查": {
        "keywords": ["review code", "代码审查", "code review", "审查代码", "PR review"],
        "steps": [
            ("code-reviewer", "代码审查", "帮我审查这段代码"),
        ],
    },
}


def cmd_recommend(query: str):
    """根据用户需求推荐 skill 工作流"""
    query_lower = query.lower()

    # 1. 匹配预设工作流
    # 去掉空格后也匹配（"写 paper" → "写paper"）
    query_nospace = query_lower.replace(" ", "")
    matched_workflows = []
    for wf_name, wf in WORKFLOW_TEMPLATES.items():
        score = 0
        for kw in wf["keywords"]:
            kw_lower = kw.lower()
            kw_nospace = kw_lower.replace(" ", "")
            # 子字符串匹配（双向）
            if kw_lower in query_lower or kw_nospace in query_nospace:
                score += 2
            # 也尝试逐词匹配
            elif any(w in query_lower for w in kw_lower.split() if len(w) >= 2):
                score += 1
        # 工作流名本身也作为关键词
        if wf_name in query_lower or wf_name.replace(" ", "") in query_nospace:
            score += 3
        if score > 0:
            matched_workflows.append((score, wf_name, wf))

    matched_workflows.sort(key=lambda x: -x[0])

    if matched_workflows:
        print(f"\n{'='*60}")
        print(f"  🧭 Skill Router — 为你的需求推荐工作流")
        print(f"{'='*60}")
        print(f"\n  📝 你的需求: {query}\n")

        for i, (score, wf_name, wf) in enumerate(matched_workflows[:3]):
            if i == 0:
                print(f"  📋 推荐工作流：{wf_name}")
                print(f"  {'─'*50}")
            else:
                print(f"\n  📋 也可参考：{wf_name}")
                print(f"  {'─'*50}")

            for j, (skill_name, desc, example) in enumerate(wf["steps"], 1):
                print(f"  步骤 {j}️⃣  → {skill_name}（{desc}）")
                print(f'         说: "{example}"')

        print(f"\n  💡 你可以从任意步骤开始，直接说对应的中文指令即可")
        print()
        return

    # 2. 没匹配到预设模板，搜索所有 skill 的描述
    skills = discover_all_skills()
    matches = []
    for s in skills:
        desc = _read_skill_description(s["path"])
        if not desc:
            continue
        # 简单关键词匹配
        desc_lower = desc.lower()
        name_lower = s["name"].lower()
        score = 0
        for word in query_lower.split():
            if len(word) < 2:
                continue
            if word in desc_lower:
                score += 2
            if word in name_lower:
                score += 3
        if score > 0:
            matches.append((score, s["name"], desc, s["root"]))

    # 去重
    seen = set()
    unique_matches = []
    for score, name, desc, root in sorted(matches, key=lambda x: -x[0]):
        if name not in seen:
            seen.add(name)
            unique_matches.append((score, name, desc, root))

    if unique_matches:
        print(f"\n{'='*60}")
        print(f"  🔍 Skill Search — 相关 Skill")
        print(f"{'='*60}")
        print(f"\n  📝 搜索: {query}\n")

        for score, name, desc, root in unique_matches[:10]:
            short_desc = desc[:80] + "…" if len(desc) > 80 else desc
            print(f"  ⭐ {name}")
            print(f"     {short_desc}")
            print()
    else:
        print(f"\n  ❌ 没找到与 \"{query}\" 相关的 skill")
        print(f"  💡 试试: python skill_manager.py list --unique  查看所有 skill")


def cmd_sync_all(yes: bool = False, force: bool = False):
    """一键同步所有 skill 到所有平台"""
    src_root = "agents"  # 以 agents 为主源
    src_dir = SKILL_ROOTS[src_root]["path"]

    if not src_dir.exists():
        print(f"❌ 主源目录不存在: {src_dir}")
        return

    targets = ["claude", "codex", "openclaw", "continue"]
    total_synced = 0

    for dst_root in targets:
        dst_dir = SKILL_ROOTS[dst_root]["path"]
        dst_dir.mkdir(parents=True, exist_ok=True)
        synced = 0

        for item in sorted(src_dir.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            dst_item = dst_dir / item.name
            if dst_item.exists() and not force:
                continue
            if not yes:
                action = "Overwrite" if dst_item.exists() else "Copy"
                resp = input(f"{action} {item.name} → {dst_root}? [y/N] ")
                if resp.lower() != "y":
                    continue
            if dst_item.exists():
                shutil.rmtree(dst_item)
            shutil.copytree(item, dst_item)
            synced += 1

        if synced:
            print(f"  ✅ {dst_root}: {synced} 个 skill 同步完成")
        total_synced += synced

    if total_synced == 0:
        print("所有平台已是最新。用 --force 强制覆盖。")
    else:
        print(f"\n总计同步 {total_synced} 个 skill")


def main():
    parser = argparse.ArgumentParser(
        description="Skill Manager v2.1 — 统一管理所有平台的 Agent Skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s list --unique        # 去重列出所有独立 skill
  %(prog)s doctor               # 健康诊断
  %(prog)s where nature-figure  # 查找 skill 位置
  %(prog)s info paper-spine     # 查看详细信息
  %(prog)s duplicates           # 列出跨平台重复
  %(prog)s sync --from claude --to agents  # 同步 skill
""",
    )
    sub = parser.add_subparsers(dest="command")

    ls = sub.add_parser("list", help="List all skills")
    ls.add_argument("--json", action="store_true", help="JSON output")
    ls.add_argument("--unique", "-u", action="store_true", help="按名字去重，合并平台信息")

    rm = sub.add_parser("remove", help="Remove a skill")
    rm.add_argument("name")
    rm.add_argument("--from", dest="from_root")
    rm.add_argument("--yes", "-y", action="store_true")

    wh = sub.add_parser("where", help="Find where a skill is installed")
    wh.add_argument("name")

    sync = sub.add_parser("sync", help="Sync skills between platforms")
    sync.add_argument("--from", dest="src", required=True)
    sync.add_argument("--to", dest="dst", required=True)
    sync.add_argument("--yes", "-y", action="store_true")
    sync.add_argument("--force", "-f", action="store_true", help="覆盖已存在的 skill")

    info = sub.add_parser("info", help="Show detailed info about a skill")
    info.add_argument("name", nargs="?", help="Skill name (or part of name)")

    sub.add_parser("usage", help="Quick reference: how to invoke each skill")
    sub.add_parser("doctor", help="健康诊断")
    sub.add_parser("duplicates", help="列出跨平台重复的 skill")

    rec = sub.add_parser("recommend", help="⭐ 根据需求推荐 skill 工作流")
    rec.add_argument("query", nargs="+", help="描述你想做什么")

    sa = sub.add_parser("sync-all", help="一键同步 agents → 所有平台")
    sa.add_argument("--yes", "-y", action="store_true")
    sa.add_argument("--force", "-f", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(json_output=getattr(args, "json", False), unique=getattr(args, "unique", False))
    elif args.command == "remove":
        cmd_remove(args.name, from_root=getattr(args, "from_root", None), yes=args.yes)
    elif args.command == "where":
        cmd_where(args.name)
    elif args.command == "sync":
        cmd_sync(args.src, args.dst, yes=args.yes, force=getattr(args, "force", False))
    elif args.command == "info":
        if args.name:
            cmd_info(args.name)
        else:
            print("Usage: skill_manager.py info <skill-name>")
            print("Try:   skill_manager.py usage   (for quick reference)")
    elif args.command == "usage":
        cmd_usage()
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "duplicates":
        cmd_duplicates()
    elif args.command == "recommend":
        cmd_recommend(" ".join(args.query))
    elif args.command == "sync-all":
        cmd_sync_all(yes=args.yes, force=getattr(args, "force", False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
