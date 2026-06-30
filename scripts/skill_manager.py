#!/usr/bin/env python3
"""
Skill Manager — 统一管理所有平台的 Agent Skills

用法:
    python skill_manager.py list [--json]
    python skill_manager.py info <name>
    python skill_manager.py usage
    python skill_manager.py where <name>
    python skill_manager.py remove <name> [--from <platform>] [--yes]
    python skill_manager.py sync --from <src> --to <dst> [--yes]
    python skill_manager.py update [--all] [--yes]
    python skill_manager.py search <keyword>
    python skill_manager.py install <github-url|owner/repo> [--skill <name>] [--yes]
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import tempfile
from pathlib import Path

HOME = Path.home()
NPX = "npx.cmd" if sys.platform == "win32" else "npx"

# 所有已知的 skill 发现路径
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
}

# Claude Code 插件目录下的 skills（如 academic-research-skills）
CLAUDE_PLUGINS_ROOT = HOME / ".claude" / "plugins" / "cache"


def discover_all_skills() -> list[dict]:
    """发现所有 skill"""
    skills = []
    seen = set()

    # 1. 标准 skill 目录
    for key, cfg in SKILL_ROOTS.items():
        skill_dir = cfg["path"]
        if not skill_dir.exists():
            continue
        for item in sorted(skill_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                skill_md = item / "SKILL.md"
                if skill_md.exists() or item.name.startswith("paper-spine"):
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
                # 找版本目录
                for ver_dir in sorted(plugin_dir.iterdir(), reverse=True):
                    skills_dir = ver_dir / "skills"
                    if not skills_dir.exists():
                        continue
                    for item in skills_dir.iterdir():
                        # 插件 skill 可能是目录（含 SKILL.md）或符号链接文件
                        name = item.name
                        is_link = item.is_file() and not item.is_symlink()
                        if item.is_dir():
                            skill_md = item / "SKILL.md"
                            has_md = skill_md.exists()
                        elif is_link:
                            # 符号链接文件：内容指向实际目录
                            has_md = True  # 假定有效
                            # 尝试读取链接目标
                            try:
                                link_target = item.read_text().strip()
                                target_dir = (item.parent / link_target).resolve()
                                if target_dir.exists():
                                    name = target_dir.name
                            except Exception:
                                pass
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

    return skills


def cmd_list(json_output: bool = False):
    """列出所有 skill"""
    skills = discover_all_skills()

    if json_output:
        print(json.dumps(skills, ensure_ascii=False, indent=2))
        return

    if not skills:
        print("No skills found.")
        return

    # 按来源分组
    by_root = {}
    for s in skills:
        by_root.setdefault(s["root"], []).append(s)

    print(f"\n{'='*70}")
    print(f"  Skill Manager — 共发现 {len(skills)} 个 Skill")
    print(f"{'='*70}")

    for root, group in sorted(by_root.items()):
        platform_str = group[0]["platforms"][0] if group else root
        method = group[0]["install_method"]
        print(f"\n📂 {root}  ({platform_str}) — {method}")
        print(f"   {'─'*50}")
        for s in group:
            status = "✅" if s["has_skill_md"] else "⚠️"
            print(f"   {status} {s['name']}")
    print()


def cmd_where(name: str):
    """查找 skill 位置"""
    skills = discover_all_skills()
    matches = [s for s in skills if s["name"] == name]

    if not matches:
        # 模糊匹配
        matches = [s for s in skills if name.lower() in s["name"].lower()]

    if not matches:
        print(f"Skill not found: {name}")
        return

    for s in matches:
        print(f"\n  {s['name']}")
        print(f"  路径: {s['path']}")
        print(f"  平台: {', '.join(s['platforms'])}")
        print(f"  安装方式: {s['install_method']}")


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
            print(f"Removed: {s['name']} ({s['root']})")
        elif target.is_file():
            target.unlink()
            print(f"Removed: {s['name']} ({s['root']}) [file]")


def cmd_sync(src_root: str, dst_root: str, yes: bool = False):
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
    for item in src_dir.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue
        dst_item = dst_dir / item.name
        if dst_item.exists():
            continue
        if not yes:
            resp = input(f"Copy {item.name} → {dst_root}? [y/N] ")
            if resp.lower() != "y":
                continue
        shutil.copytree(item, dst_item)
        print(f"Synced: {item.name} → {dst_root}")
        synced += 1

    if synced == 0:
        print("Nothing to sync.")


# ── Skill 来源追踪（用于一键更新）────────────────────────────────

SKILL_SOURCES = {
    # paper-craft 套件（来自 npx skills add / zsyggg/paper-craft-skills）
    "paper-analyzer": {
        "type": "github",
        "repo": "https://github.com/zsyggg/paper-craft-skills.git",
        "install_cmd": 'npx skills add https://github.com/zsyggg/paper-craft-skills --skill paper-analyzer -y',
        "method": "npx skills add",
    },
    "paper-comic": {
        "type": "github",
        "repo": "https://github.com/zsyggg/paper-craft-skills.git",
        "install_cmd": 'npx skills add https://github.com/zsyggg/paper-craft-skills --skill paper-comic -y',
        "method": "npx skills add",
    },
    "paper-deck": {
        "type": "github",
        "repo": "https://github.com/zsyggg/paper-craft-skills.git",
        "install_cmd": 'npx skills add https://github.com/zsyggg/paper-craft-skills --skill paper-deck -y',
        "method": "npx skills add",
    },
    # PaperSpine 套件（来自 git clone + install.ps1）
    "paper-spine": {
        "type": "github",
        "repo": "https://github.com/WUBING2023/PaperSpine.git",
        "local_clone": str(HOME / "PaperSpine"),
        "reinstall_cmd": 'cd /d C:\\Users\\A\\PaperSpine && git pull && powershell -ExecutionPolicy Bypass -File install.ps1 -Target all -CleanLegacy',
        "method": "git clone + install.ps1",
    },
    # Academic Research Skills（Claude Code 插件）
    "academic-paper": {
        "type": "claude-plugin",
        "plugin": "academic-research-skills@academic-research-skills",
        "update_cmd": "claude plugins update academic-research-skills@academic-research-skills",
        "method": "Claude Code plugin",
    },
    # skill-manager 自身
    "skill-manager": {
        "type": "self",
        "method": "手动创建 (本地)",
    },
    # nature-skills 套件（来自 npx skills add / yuan1z0825/nature-skills）
    "nature-figure": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-figure -y",
        "method": "npx skills add",
    },
    "nature-polishing": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-polishing -y",
        "method": "npx skills add",
    },
    "nature-paper2ppt": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-paper2ppt -y",
        "method": "npx skills add",
    },
    "nature-data": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-data -y",
        "method": "npx skills add",
    },
    "nature-citation": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-citation -y",
        "method": "npx skills add",
    },
    "nature-response": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-response -y",
        "method": "npx skills add",
    },
    "nature-writing": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-writing -y",
        "method": "npx skills add",
    },
    "nature-reviewer": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-reviewer -y",
        "method": "npx skills add",
    },
    "nature-reader": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-reader -y",
        "method": "npx skills add",
    },
    "nature-academic-search": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-academic-search -y",
        "method": "npx skills add",
    },
    "nature-literature-pipeline": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-literature-pipeline -y",
        "method": "npx skills add",
    },
    "nature-downloader": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-downloader -y",
        "method": "npx skills add",
    },
    "nature-paper-to-patent": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill nature-paper-to-patent -y",
        "method": "npx skills add",
    },
    "researchwrite": {
        "type": "github", "repo": "https://github.com/yuan1z0825/nature-skills.git",
        "install_cmd": "npx skills add yuan1z0825/nature-skills --skill researchwrite -y",
        "method": "npx skills add",
    },
    # Grant Writer 套件（来自 HuiyuLi-2000/Chinese-Grant-Writer-Skills）
    "fund-background-writer": {
        "type": "github", "repo": "https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git",
        "install_cmd": "npx skills add HuiyuLi-2000/Chinese-Grant-Writer-Skills --skill fund-background-writer -y",
        "method": "npx skills add",
    },
    "fund-literature-review-writer": {
        "type": "github", "repo": "https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git",
        "install_cmd": "npx skills add HuiyuLi-2000/Chinese-Grant-Writer-Skills --skill fund-literature-review-writer -y",
        "method": "npx skills add",
    },
    "fund-research-content-writer": {
        "type": "github", "repo": "https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git",
        "install_cmd": "npx skills add HuiyuLi-2000/Chinese-Grant-Writer-Skills --skill fund-research-content-writer -y",
        "method": "npx skills add",
    },
    "fund-technical-route-writer": {
        "type": "github", "repo": "https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills.git",
        "install_cmd": "npx skills add HuiyuLi-2000/Chinese-Grant-Writer-Skills --skill fund-technical-route-writer -y",
        "method": "npx skills add",
    },
    "code-reviewer": {
        "type": "github", "repo": "https://github.com/google-gemini/gemini-cli.git",
        "install_cmd": "npx skills add google-gemini/gemini-cli --skill code-reviewer -y",
        "method": "npx skills add",
    },
    "posterskill-academic-posters": {
        "type": "github", "repo": "https://github.com/aradotso/trending-skills.git",
        "install_cmd": "npx skills add aradotso/trending-skills --skill posterskill-academic-posters -y",
        "method": "npx skills add",
    },
}

# PaperSpine 所有子 skill 共享同一个更新源
for _sub in ["paper-spine-audit", "paper-spine-build", "paper-spine-citation",
             "paper-spine-humanize", "paper-spine-intake", "paper-spine-latex",
             "paper-spine-research", "paper-spine-rewrite", "paper-spine-translate",
             "paper-spine-ui", "paper-spine-update"]:
    SKILL_SOURCES[_sub] = SKILL_SOURCES["paper-spine"]

# Academic Research Skills 插件所有子 skill
for _sub in ["academic-paper-reviewer", "academic-pipeline", "deep-research"]:
    SKILL_SOURCES[_sub] = SKILL_SOURCES["academic-paper"]

SKILL_USAGE = {
    "paper-analyzer": {
        "how": "/paper-analyzer <arxiv-url|pdf路径|粘贴文本>",
        "example": '/paper-analyzer https://arxiv.org/abs/1706.03762',
        "platforms": "Copilot / Cline",
        "note": "也支持自然语言：\"帮我分析这篇论文\"",
    },
    "paper-comic": {
        "how": "/paper-comic <pdf|arxiv-url> [--style sketchnote|paper-figure] [--language zh|en]",
        "example": "/paper-comic paper.pdf --style sketchnote",
        "platforms": "Copilot / Cline",
        "note": "先生成方案让你确认，确认后才出图",
    },
    "paper-deck": {
        "how": "/paper-deck <pdf|arxiv-url> [--style journal-minimal] [--slides 12]",
        "example": "/paper-deck https://arxiv.org/abs/1706.03762 --slides 12",
        "platforms": "Copilot / Cline",
        "note": "也支持关键词触发：\"论文PPT\"\"把论文做成幻灯片\"",
    },
    "paper-spine": {
        "how": "/paperspine",
        "example": "/paperspine",
        "platforms": "Claude Code / Cline",
        "note": "主控 skill，自动路由到配置 UI → 调研 → 引用 → 写作 → LaTeX → 审计",
    },
    "paper-spine-humanize": {
        "how": "自动调用（paper-spine 内部步骤 #8）",
        "example": "在 paper_spine_config.json 中设置 humanize_tier 为 light/medium/heavy",
        "platforms": "Claude Code / Cline",
        "note": "降 AIGC 检测率；也可独立使用：\"用 paper-spine-humanize 降重\"",
    },
    "paper-spine-audit": {
        "how": "自动调用（paper-spine 内部步骤 #7）",
        "example": "python src/scripts/artifact_check.py paper_rewriting_output --markdown",
        "platforms": "Claude Code / Cline",
        "note": "检查产物完整性、写作深度、引用库质量",
    },
    "paper-spine-research": {
        "how": "自动调用（paper-spine 内部步骤 #3）",
        "example": "无直接调用",
        "platforms": "Claude Code / Cline",
        "note": "调研目标场景要求、下载参考材料、学习优秀样例",
    },
    "paper-spine-citation": {
        "how": "自动调用（paper-spine 内部步骤 #4）",
        "example": "无直接调用",
        "platforms": "Claude Code / Cline",
        "note": "构建 Introduction/Discussion 的逐句 claim 引用支持库",
    },
    "paper-spine-rewrite": {
        "how": "自动调用（paper-spine 内部步骤 #5a）",
        "example": "无直接调用",
        "platforms": "Claude Code / Cline",
        "note": "基于已确认动机+研究+证据改写已有论文",
    },
    "paper-spine-build": {
        "how": "自动调用（paper-spine 内部步骤 #5b）",
        "example": "无直接调用",
        "platforms": "Claude Code / Cline",
        "note": "从素材文件夹（图片/PDF/数据摘要/初稿）构筑论文",
    },
    "paper-spine-latex": {
        "how": "自动调用（paper-spine 内部步骤 #6）",
        "example": "python src/scripts/latex_guard.py paper_rewriting_output/final_paper/main.tex",
        "platforms": "Claude Code / Cline",
        "note": "组装 LaTeX 项目、图表排版、引用标签、编译检查",
    },
    "paper-spine-translate": {
        "how": "自动调用（paper-spine 内部步骤 #9）",
        "example": "无直接调用",
        "platforms": "Claude Code / Cline",
        "note": "产出完整 translation_zh/ 翻译包（逐行翻译所有中间产物）",
    },
    "paper-spine-intake": {
        "how": "自动调用（paper-spine 内部步骤 #2）",
        "example": "无直接调用",
        "platforms": "Claude Code / Cline",
        "note": "校验/修复 paper_spine_config.json 配置",
    },
    "paper-spine-ui": {
        "how": "自动调用（paper-spine 内部步骤 #1）或 python src/scripts/intake_wizard.py",
        "example": "python src/scripts/intake_wizard.py",
        "platforms": "Claude Code / Cline",
        "note": "终端交互式配置向导（选场景/深度/语言/降重等级等）",
    },
    "paper-spine-update": {
        "how": '自然语言："检查 PaperSpine 更新""升级 PaperSpine"',
        "example": "python scripts/paperspine_update.py --yes",
        "platforms": "Claude Code / Cline",
        "note": "从 GitHub 拉取最新版，保留全局配置",
    },
    "academic-paper": {
        "how": '自然语言触发："write paper""academic paper""写论文""學術論文"',
        "example": "启动后按模式选择：10 modes, 6 paper types, 5 citation formats",
        "platforms": "Claude Code (插件)",
        "note": "12-agent 论文写作流水线，输出 LaTeX/DOCX/PDF",
    },
    "academic-paper-reviewer": {
        "how": '自然语言触发："review paper""peer review""审稿"',
        "example": "启动后模拟 5 位审稿人（EIC + 3 reviewers + Devil's Advocate）",
        "platforms": "Claude Code (插件)",
        "note": "多视角学术论文审稿，6 种模式",
    },
    "academic-pipeline": {
        "how": '自然语言触发："academic pipeline""full paper workflow""论文全流程"',
        "example": "启动后走 10 阶段：research → write → review → revise → finalize",
        "platforms": "Claude Code (插件)",
        "note": "编排 research + paper + reviewer 三个 skill 的完整流水线",
    },
    "deep-research": {
        "how": '自然语言触发："deep research""文献综述""深度研究""systematic review"',
        "example": "启动后选 7 种模式之一，13-agent 流水线",
        "platforms": "Claude Code (插件)",
        "note": "通用深度研究，支持 PRISMA 系统综述 + meta-analysis",
    },
    "skill-manager": {
        "how": '自然语言："管理 skill""列出所有 skill""删除 xx skill"',
        "example": 'python ~/.agents/skills/skill-manager/scripts/skill_manager.py list',
        "platforms": "Copilot / Cline",
        "note": "统一管理所有平台的 skill（本工具）",
    },
    # nature-skills 套件
    "nature-figure": {
        "how": '自然语言："Nature figure""投稿级图片""publication plot""科学绘图"',
        "example": '帮我把这个数据画成 Nature 投稿级图表',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "Python/R 科研绘图，内置 figures4papers demo",
    },
    "nature-polishing": {
        "how": '自然语言："Nature style""润色""academic writing""论文英文"',
        "example": '把这段中文摘要润色成 Nature 风格英文',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "学术文本润色/重构/翻译为 Nature 风格",
    },
    "nature-writing": {
        "how": '自然语言："Nature writing""写摘要""写引言""manuscript draft"',
        "example": '帮我起草这篇论文的 Introduction，Nature 风格',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "起草 Nature 风格手稿章节",
    },
    "nature-reviewer": {
        "how": '自然语言："Nature reviewer""预投稿评审""审稿人视角评估"',
        "example": '模拟 Nature 审稿人帮我审这篇论文',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "模拟 3 位审稿人 + 综合意见",
    },
    "nature-citation": {
        "how": '自然语言："Nature citation""CNS citation""分段引用""Zotero"',
        "example": '帮我找这篇论文的 Nature/CNS 级别支撑引用',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "检索限定 Nature/CNS 系列的文献，导出 ENW/RIS/Zotero",
    },
    "nature-data": {
        "how": '自然语言："Data Availability""数据可用性""FAIR metadata"',
        "example": '帮我写 Data Availability Statement',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "准备数据可用性声明、仓储方案和 FAIR 检查",
    },
    "nature-reader": {
        "how": '自然语言："nature reader""全文 Markdown""原文对照""全文翻译"',
        "example": '把这篇论文转成中英对照的 Markdown reader',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "生成带来源锚点、图文对应和中英文对照的全文 Markdown",
    },
    "nature-response": {
        "how": '自然语言："response to reviewers""rebuttal letter""审稿意见回复"',
        "example": '帮我起草回复审稿人的 response letter',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "起草、审查和修改逐点回复审稿人的信件",
    },
    "nature-paper2ppt": {
        "how": '自然语言："paper PPT""journal club""paper to slides""论文汇报"',
        "example": '把这篇论文做成中文文献汇报 PPT',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "生成中文 PPTX 文献汇报 deck",
    },
    "nature-paper-to-patent": {
        "how": '自然语言："paper to patent""Chinese patent""论文转专利"',
        "example": '帮我把这篇论文转成中国发明专利草稿',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "有证据约束的发明专利草稿生成",
    },
    "nature-academic-search": {
        "how": '自然语言："search papers""查文献""find articles""verify DOI"',
        "example": '帮我搜索 XXX 领域的最新论文',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "多源文献检索、引用核验和参考文献管理",
    },
    "nature-literature-pipeline": {
        "how": '自然语言："literature pipeline""每日文献""文献推送"',
        "example": '帮我设置每日文献自动推送管线',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "自动化文献发现：检索→六维评分→推送→归档",
    },
    "nature-downloader": {
        "how": '自然语言："download papers""图书馆下载文献""CARSI""PDF 下载"',
        "example": '帮我通过 CARSI 下载这篇论文的 PDF',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "通过图书馆资源、CARSI 等合法获取全文 PDF",
    },
    "researchwrite": {
        "how": '自然语言："researchwrite""proposal""开题报告""研究方案"',
        "example": '帮我写一份研究方案/开题报告',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "proposal-first 科研写作状态机",
    },
    # Grant Writer 套件
    "fund-background-writer": {
        "how": '自然语言："写立项依据""研究意义""项目背景""NSFC背景"',
        "example": '帮我写国自然基金的立项依据和研究意义',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "撰写 NSFC 申请书立项依据/研究意义/项目背景",
    },
    "fund-literature-review-writer": {
        "how": '自然语言："国内外研究现状""文献综述""文献评述""NSFC 1.2"',
        "example": '帮我写国自然基金的国内外研究现状和文献评述',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "撰写 NSFC 国内外研究现状及发展动态分析",
    },
    "fund-research-content-writer": {
        "how": '自然语言："研究内容""关键科学问题""研究目标""NSFC方案"',
        "example": '帮我拆解研究内容、凝练关键科学问题',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "NSFC 研究目标-研究内容-关键科学问题。默认面上，支持重点/青年/省基金",
    },
    "fund-technical-route-writer": {
        "how": '自然语言："技术路线""研究方法""创新特色""NSFC路线"',
        "example": '帮我写技术路线和创新点',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "NSFC 研究方法、技术路线与创新特色，支持学术化表达和逻辑优化",
    },
    "code-reviewer": {
        "how": '自然语言："code review""审查代码""检查仿真""找bug"',
        "example": '帮我审查这段 MATLAB 仿真代码',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "Google 官方出品，代码质量审查、bug 检测、优化建议",
    },
    "posterskill-academic-posters": {
        "how": '自然语言："学术海报""conference poster""会议海报""poster"',
        "example": '帮我做一个 ICC 会议的学术海报',
        "platforms": "Copilot / Cline / Claude Code",
        "note": "生成学术会议海报，含标题/作者/图表/结论布局",
    },
}


def _read_skill_description(skill_path_str: str) -> str:
    """从 SKILL.md 读取 description"""
    skill_md = Path(skill_path_str) / "SKILL.md"
    if not skill_md.exists():
        return ""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        # 解析 YAML frontmatter
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                fm = text[3:end].strip()
                for line in fm.split("\n"):
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
                        if desc.startswith("|"):
                            # 多行描述 (|)
                            body_start = end + 3
                            desc_body = text[body_start:body_start+300].strip()
                            return desc_body[:200]
                        return desc[:200]
    except Exception:
        pass
    return ""


def cmd_info(name: str):
    """查看 skill 详细信息"""
    skills = discover_all_skills()
    matches = [s for s in skills if s["name"].lower() == name.lower()]

    if not matches:
        matches = [s for s in skills if name.lower() in s["name"].lower()]

    if not matches:
        print(f"Skill not found: {name}")
        return

    for s in matches:
        usage = SKILL_USAGE.get(s["name"], {})
        desc = _read_skill_description(s["path"]) or usage.get("note", "")

        print(f"\n{'='*60}")
        print(f"  {s['name']}")
        print(f"{'='*60}")
        print(f"  描述: {desc}")
        print(f"  安装位置: {s['path']}")
        print(f"  可用平台: {', '.join(s['platforms'])}")
        print(f"  安装方式: {s['install_method']}")

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
    print(f"  {'Skill':<26} {'调用方式':<48}")
    print(f"  {'─'*26} {'─'*48}")

    for name, info in sorted(SKILL_USAGE.items()):
        how = info["how"]
        if len(how) > 46:
            how = how[:44] + "…"
        print(f"  {name:<26} {how:<48}")

    print(f"\n  💡 提示：绝大部分 paper-spine-* 子 skill 由 /paperspine 自动调用，无需手动触发")
    print(f"  💡 academic-* 系列由关键词触发，直接描述需求即可")
    print()


# ── 更新 ─────────────────────────────────────────────────────────

def cmd_update(all_skills: bool = False, yes: bool = False):
    """一键更新已安装的 skill"""
    skills = discover_all_skills()
    unique = {}
    for s in skills:
        if s["name"] not in unique:
            unique[s["name"]] = s

    print(f"\n🔄 检查 {len(unique)} 个 skill 的更新...\n")

    updated = 0
    skipped = 0
    failed = 0

    for name in sorted(unique.keys()):
        source = SKILL_SOURCES.get(name, {})
        stype = source.get("type", "unknown")

        if stype == "github":
            repo = source.get("repo", "")
            method = source.get("method", "git")
            local = source.get("local_clone", "")

            if method == "npx skills add":
                print(f"  📦 {name} (npx skills add)")
                if not yes:
                    resp = input(f"     更新? [y/N] ").lower()
                    if resp != "y":
                        skipped += 1
                        continue
                cmd = source.get("install_cmd", "")
                if cmd:
                    print(f"     运行: npx skills update {name} ...")
                    try:
                        subprocess.run([NPX, "skills", "update", name], check=False, timeout=120)
                        print(f"     ✅ {name} 已更新")
                        updated += 1
                    except Exception as e:
                        print(f"     ❌ 失败: {e}")
                        failed += 1

            elif method == "git clone + install.ps1":
                print(f"  📦 {name} (PaperSpine)")
                if local and Path(local).exists():
                    if not yes:
                        resp = input(f"     git pull + reinstall? [y/N] ").lower()
                        if resp != "y":
                            skipped += 1
                            continue
                    print(f"     git pull {local}...")
                    try:
                        subprocess.run(["git", "-C", local, "pull"], check=True, timeout=60)
                        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass",
                                       "-File", str(Path(local) / "install.ps1"),
                                       "-Target", "all", "-CleanLegacy"], check=False, timeout=120)
                        print(f"     ✅ {name} (PaperSpine 套件) 已更新")
                        updated += 1
                        # 只更新一次，跳过同套件的其他 skill
                        break
                    except Exception as e:
                        print(f"     ❌ 失败: {e}")
                        failed += 1
                        break
                else:
                    print(f"     ⚠️ 本地克隆不存在: {local}")
                    skipped += 1

        elif stype == "claude-plugin":
            print(f"  📦 {name} (Claude Code 插件)")
            plugin = source.get("plugin", "")
            print(f"     请在 Claude Code 中运行: claude plugins update {plugin}")
            skipped += 1
            # 跳过同套件其他 skill
            for sub in ["academic-paper-reviewer", "academic-pipeline", "deep-research"]:
                if sub in unique:
                    del unique[sub]
            break

        elif stype == "self":
            print(f"  📦 {name} (本地 skill-manager — 已是最新)")
            skipped += 1

        else:
            print(f"  📦 {name} (未知来源 — 跳过)")
            skipped += 1

    print(f"\n{'='*50}")
    print(f"  更新完成: ✅ {updated}  |  ⏭️ {skipped}  |  ❌ {failed}")
    print(f"{'='*50}\n")


# ── 搜索 ─────────────────────────────────────────────────────────

def cmd_search(keyword: str):
    """搜索 GitHub 和 skills.sh 上的新 skill"""
    print(f"\n🔍 搜索: \"{keyword}\"\n")

    # 1. 使用 npx skills find
    print("─" * 50)
    print("  📡 skills.sh marketplace (npx skills find)")
    print("─" * 50)
    try:
        result = subprocess.run(
            [NPX, "skills", "find", keyword, "--json"],
            capture_output=True, text=True, timeout=60
        )
        if result.stdout.strip():
            print(result.stdout[:3000])
        else:
            print("  (无结果或需要交互模式)")
    except Exception as e:
        print(f"  npx skills find 不可用: {e}")

    # 2. GitHub 搜索
    print("\n" + "─" * 50)
    print("  📡 GitHub 仓库搜索")
    print("─" * 50)
    try:
        query = urllib.parse.quote(f"{keyword} skill SKILL.md")
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=10"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", [])[:10]:
                stars = item.get("stargazers_count", 0)
                desc = (item.get("description") or "")[:100]
                print(f"  ⭐{stars:<6} {item['full_name']}")
                if desc:
                    print(f"          {desc}")
                print(f"          {item['html_url']}")
    except Exception as e:
        print(f"  GitHub API 不可用: {e}")

    # 3. 提示安装命令
    print(f"\n💡 找到想要的 skill 后，运行:")
    print(f"   python skill_manager.py install <owner/repo>")
    print(f"   或")
    print(f"   npx skills add <owner/repo>\n")


# ── 安装 ─────────────────────────────────────────────────────────

def cmd_install(source: str, skill_name: str = None, yes: bool = False):
    """从 GitHub 安装新 skill"""
    print(f"\n📥 安装: {source}")

    # 判断是 owner/repo 还是完整 URL
    if source.startswith("http"):
        if "github.com" in source:
            parts = source.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1].replace(".git", "")
            source = f"{owner}/{repo}"
        else:
            print(f"  仅支持 GitHub 仓库")
            return

    if "/" not in source:
        print(f"  格式错误。请使用 owner/repo 或完整 GitHub URL")
        return

    cmd = [NPX, "skills", "add", source]
    if skill_name:
        cmd.extend(["--skill", skill_name])
    if yes:
        cmd.append("-y")

    print(f"  运行: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=False, timeout=300)
        print(f"  ✅ 安装完成")
        print(f"  运行 python skill_manager.py list 查看新 skill")
    except Exception as e:
        print(f"  ❌ 安装失败: {e}")


# ── Agent 浏览器 ───────────────────────────────────────────────────

def _discover_agents(skill_path: str) -> list[dict]:
    """扫描 skill 内部的 agents/ 目录"""
    agents = []

    # 直接路径
    agents_dir = Path(skill_path) / "agents"
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            _parse_agent_file(f, agents)

    # 插件 skill：path 可能是文件（symlink），需要找实际目录
    if not agents:
        p = Path(skill_path)
        if p.is_file():
            # 尝试读取链接目标
            try:
                target = p.read_text().strip()
                real_dir = (p.parent / target).resolve()
                if real_dir.exists():
                    agents_dir2 = real_dir / "agents"
                    if agents_dir2.exists():
                        for f in sorted(agents_dir2.glob("*.md")):
                            _parse_agent_file(f, agents)
            except Exception:
                pass

    # 仍在附近搜索（插件结构：skills/skill-name 对应 ../skill-name/agents/）
    if not agents:
        p = Path(skill_path)
        if not p.is_dir():
            parent = p.parent.parent  # 上两级到插件根
            for candidate in parent.glob(f"*{p.stem}*"):
                if candidate.is_dir():
                    agents_dir3 = candidate / "agents"
                    if agents_dir3.exists():
                        for f in sorted(agents_dir3.glob("*.md")):
                            _parse_agent_file(f, agents)
                        break

    return agents


def _parse_agent_file(f: Path, agents: list):
    """解析单个 agent 文件"""
    try:
        text = f.read_text(encoding="utf-8", errors="replace")
        name = f.stem.replace("_", " ").title()
        desc = ""
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                fm = text[3:end]
                for line in fm.split("\n"):
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                        break
        if not desc:
            for line in text.split("\n")[:5]:
                stripped = line.strip()
                if stripped.startswith("# "):
                    desc = stripped.strip("# ").strip()
                    break
                if stripped and not stripped.startswith("---"):
                    desc = stripped[:80]
                    break
        agents.append({"name": name, "file": f.name, "desc": desc or "(无描述)"})
    except Exception:
        pass


def _discover_references(skill_path: str) -> list[dict]:
    """扫描 skill 内部的 references/ 目录，提取关键能力"""
    refs = []
    ref_dir = Path(skill_path) / "references"
    if not ref_dir.exists():
        return refs
    keywords = ["stat", "repro", "survey", "cite", "review", "audit", "integrity",
                "figure", "table", "visual", "proofread", "format", "template"]
    for f in sorted(ref_dir.glob("*.md")):
        name = f.stem.replace("_", " ").title()
        if any(kw in name.lower() for kw in keywords):
            refs.append({"name": name, "file": f.name, "type": "reference"})
    return refs


def cmd_agents(skill_name: str = None):
    """列出某 skill 的所有内部 Agent"""
    if not skill_name:
        print("用法: skill_manager.py agents <skill-name>")
        print("试试: skill_manager.py agents academic-paper-reviewer")
        return

    skills = discover_all_skills()
    matches = [s for s in skills if skill_name.lower() in s["name"].lower()]
    if not matches:
        print(f"未找到: {skill_name}")
        return

    for s in matches[:3]:  # 最多展示 3 个匹配
        print(f"\n{'='*60}")
        print(f"  {s['name']}")
        print(f"{'='*60}")

        agents = _discover_agents(s["path"])
        refs = _discover_references(s["path"])

        if agents:
            print(f"\n  🤖 内部 Agent ({len(agents)} 个):")
            for a in agents:
                print(f"     • {a['name']:<30} {a['desc'][:55]}")
        else:
            print(f"\n  ⚠️ 无独立 Agent 目录（该 skill 为单 agent 模式）")

        if refs:
            print(f"\n  📚 关键参考能力 ({len(refs)} 个):")
            for r in refs:
                print(f"     📄 {r['name']}")

    # 查找所有有 agent 的 skill
    if not skill_name:
        print(f"\n💡 以下 skill 包含内部 Agent：")
        for s in skills:
            agents = _discover_agents(s["path"])
            if agents:
                print(f"   {s['name']} ({len(agents)} agents)")


# ── 工作流顾问 ─────────────────────────────────────────────────────

WORKFLOWS = {
    "初稿到发表": {
        "desc": "从一篇初稿开始，逐步打磨到可投稿/发表的水平",
        "steps": [
            {"step": 1, "action": "自我审查", "skill": "nature-reviewer / academic-paper-reviewer",
             "what": "模拟 3-5 位审稿人评审你的初稿，找出逻辑漏洞、方法缺陷、统计学问题",
             "trigger": '"帮我审这篇稿子"'},
            {"step": 2, "action": "统计验证", "skill": "academic-paper-reviewer (methodology_reviewer + field_analyst)",
             "what": "检查统计方法是否正确、效应量是否报告、p值是否合理",
             "trigger": '"审查这篇论文的统计方法"'},
            {"step": 3, "action": "学术润色", "skill": "nature-polishing / paper-spine-humanize",
             "what": "将语言润色到 Nature 期刊水平，同时降低 AIGC 检测率",
             "trigger": '"帮我润色这篇论文" 或 "Nature style"'},
            {"step": 4, "action": "引用补强", "skill": "nature-citation / paper-spine-citation",
             "what": "为每个 claim 找到 CNS 级别的支撑文献，构建引用库",
             "trigger": '"帮我找这篇论文的支撑引用"'},
            {"step": 5, "action": "作图升级", "skill": "nature-figure",
             "what": "将图表重绘为 Nature 投稿级别（600dpi, 指定字体, 色彩规范）",
             "trigger": '"帮我把这个图画成 Nature 风格"'},
            {"step": 6, "action": "Data Availability", "skill": "nature-data",
             "what": "准备数据可用性声明、仓储方案、FAIR 合规检查",
             "trigger": '"帮我写 Data Availability Statement"'},
            {"step": 7, "action": "LaTeX 排版", "skill": "paper-spine-latex / academic-paper",
             "what": "组装 LaTeX 项目，处理图表引用、交叉引用、参考文献格式",
             "trigger": '"帮我排 LaTeX" 或 "帮我生成 PDF"'},
            {"step": 8, "action": "最终审计", "skill": "paper-spine-audit",
             "what": "检查产物完整性、写作深度、引用质量、翻译覆盖率",
             "trigger": '"帮我审计这篇论文"'},
        ]
    },
    "文献综述": {
        "desc": "系统性地调研一个领域，产出综述文章",
        "steps": [
            {"step": 1, "action": "深度搜索", "skill": "nature-academic-search",
             "what": "多源检索（PubMed/CrossRef/arXiv/Scopus），去重，导出 BibTeX",
             "trigger": '"帮我搜索 XXX 领域的所有论文"'},
            {"step": 2, "action": "文献筛选", "skill": "deep-research (PRISMA protocol)",
             "what": "按 PRISMA 标准筛选、去重、质量评估",
             "trigger": '"做一篇 XXX 的系统综述"'},
            {"step": 3, "action": "全文获取", "skill": "nature-downloader",
             "what": "通过 CARSI/图书馆/开放获取获取全文 PDF",
             "trigger": '"帮我下载这些论文的 PDF"'},
            {"step": 4, "action": "深度阅读", "skill": "nature-reader / paper-analyzer",
             "what": "生成中英对照的全文 Markdown reader，图文对应",
             "trigger": '"把这批论文转成 reader"'},
            {"step": 5, "action": "综述写作", "skill": "nature-writing / academic-paper",
             "what": "起草综述各章节（引言/方法/结果/讨论/结论）",
             "trigger": '"帮我写这篇综述"'},
        ]
    },
    "审稿回复": {
        "desc": "收到审稿意见后，逐点回复并修改",
        "steps": [
            {"step": 1, "action": "解析审稿意见", "skill": "nature-response",
             "what": "自动分类审稿意见（major/minor/format），生成回复模板",
             "trigger": '"帮我起草 response letter"'},
            {"step": 2, "action": "补充实验/分析", "skill": "nature-figure + paper-spine-build",
             "what": "根据审稿意见补充图表、消融实验、统计检验",
             "trigger": '"审稿人要求补充 XX 实验"'},
            {"step": 3, "action": "逐点修改", "skill": "paper-spine-rewrite",
             "what": "根据每条审稿意见修改正文对应段落",
             "trigger": '"按审稿意见修改论文"'},
            {"step": 4, "action": "润色回复信", "skill": "nature-polishing",
             "what": "润色 response letter 的语言和语气",
             "trigger": '"润色我的回复信"'},
        ]
    },
    "基金申请": {
        "desc": "撰写国自然/博士基金申请书",
        "steps": [
            {"step": 1, "action": "文献调研", "skill": "nature-literature-pipeline + deep-research",
             "what": "自动化文献发现管线，找到立项依据",
             "trigger": '"调研 XXX 方向的文献"'},
            {"step": 2, "action": "研究方案起草", "skill": "researchwrite / nature-proposal-writer",
             "what": "proposal-first 写作：先建立证据和论证，再写正文",
             "trigger": '"帮我写研究方案"'},
            {"step": 3, "action": "预算与路线图", "skill": "researchwrite",
             "what": "生成研究路线图、时间表、预算说明",
             "trigger": '"帮我做研究计划的时间表"'},
            {"step": 4, "action": "润色与合规", "skill": "nature-polishing",
             "what": "润色申请书语言，检查格式合规",
             "trigger": '"润色我的基金申请书"'},
        ]
    },
    "投前自查": {
        "desc": "投稿前全面检查论文质量",
        "steps": [
            {"step": 1, "action": "格式检查", "skill": "paper-spine-latex / academic-paper (formatter_agent)",
             "what": "检查期刊模板、页数、图表格式、参考文献格式",
             "trigger": '"检查论文格式是否符合 XX 期刊要求"'},
            {"step": 2, "action": "引用完整性", "skill": "nature-citation + source_verification_agent",
             "what": "验证每个引用是否真实存在、是否与正文对应",
             "trigger": '"验证论文引用的真实性"'},
            {"step": 3, "action": "图表质量", "skill": "nature-figure",
             "what": "检查图表分辨率、色彩空间、字体、标注完整性",
             "trigger": '"检查图表是否符合投稿标准"'},
            {"step": 4, "action": "学术诚信", "skill": "academic-pipeline (integrity_verification + plagiarism_check)",
             "what": "查重、AI 痕迹检测、数据完整性验证",
             "trigger": '"检查这篇论文的学术诚信"'},
            {"step": 5, "action": "最终审稿模拟", "skill": "nature-reviewer",
             "what": "最后一遍预投稿评审",
             "trigger": '"最后帮我审一遍"'},
        ]
    },
    "从头写论文": {
        "desc": "从零开始写一篇完整论文",
        "steps": [
            {"step": 1, "action": "确认方向与动机", "skill": "paper-spine-research",
             "what": "调研目标期刊/会议要求，学习优秀样例，确认论文动机",
             "trigger": '"帮我调研 ICC/TWC 的投稿要求"'},
            {"step": 2, "action": "搭建论文框架", "skill": "academic-paper (structure_architect + argument_builder)",
             "what": "设计论文结构，构建核心论证链",
             "trigger": '"帮我设计论文结构"'},
            {"step": 3, "action": "起草各章节", "skill": "nature-writing / academic-paper (draft_writer)",
             "what": "逐章起草：Abstract → Introduction → Method → Results → Discussion",
             "trigger": '"帮我起草论文各部分"'},
            {"step": 4, "action": "生成图表", "skill": "nature-figure + paper-comic",
             "what": "根据数据生成投稿级图表",
             "trigger": '"帮我把数据画成论文图"'},
            {"step": 5, "action": "内部审稿+修改", "skill": "nature-reviewer → paper-spine-rewrite",
             "what": "模拟审稿 → 根据意见修改 → 再审",
             "trigger": '"审稿后帮我修改"'},
            {"step": 6, "action": "最终输出", "skill": "paper-spine-latex",
             "what": "输出 LaTeX/PDF/Word",
             "trigger": '"帮我生成最终 PDF"'},
        ]
    },
}


def cmd_advise(query: str = None):
    """根据用户描述推荐工作流"""
    print(f"\n{'='*65}")
    print(f"  🧭 Skill Manager — 工作流顾问")
    print(f"{'='*65}")

    if not query:
        print(f"\n  可用的预设工作流：\n")
        for name, wf in WORKFLOWS.items():
            print(f"  📋 {name}")
            print(f"     {wf['desc']}")
            print(f"     {len(wf['steps'])} 步完成")
            print()
        print(f"  用法: skill_manager.py advise \"你的需求描述\"")
        print(f"  例如: skill_manager.py advise \"我有一篇初稿想投 ICC\"")
        return

    query_lower = query.lower()

    # 关键词匹配
    matched = None
    best_score = 0
    for name, wf in WORKFLOWS.items():
        score = 0
        wf_lower = (name + wf["desc"]).lower()
        for word in query_lower.split():
            if word in wf_lower:
                score += 1
        # 额外关键词加权
        if any(kw in query_lower for kw in ["初稿", "draft", "初版", "草稿"]):
            if "初稿" in name:
                score += 3
        if any(kw in query_lower for kw in ["审稿", "review", "回复", "rebuttal"]):
            if "审稿" in name:
                score += 3
        if any(kw in query_lower for kw in ["综述", "review", "survey", "文献"]):
            if "文献" in name:
                score += 3
        if any(kw in query_lower for kw in ["基金", "grant", "申请", "国自然"]):
            if "基金" in name:
                score += 3
        if any(kw in query_lower for kw in ["投稿", "submit", "提交", "投前"]):
            if "投前" in name:
                score += 3
        if any(kw in query_lower for kw in ["写", "write", "new", "新", "从零"]):
            if "从头" in name:
                score += 3
        if score > best_score:
            best_score = score
            matched = name

    if not matched or best_score == 0:
        print(f"\n  未匹配到精确工作流，最接近的推荐：\n")
        matched = "初稿到发表"  # 默认

    wf = WORKFLOWS[matched]
    print(f"\n  📋 推荐工作流: {matched}")
    print(f"  📝 {wf['desc']}")
    print(f"\n  {'─'*55}")
    for s in wf["steps"]:
        print(f"  Step {s['step']}: {s['action']}")
        print(f"     🔧 使用: {s['skill']}")
        print(f"     📖 {s['what']}")
        print(f"     💬 说: {s['trigger']}")
        print()

    # 额外建议
    print(f"  {'─'*55}")
    print(f"  💡 也可以查看更详细的 agent 列表:")
    for s in wf["steps"]:
        skill_name = s["skill"].split("/")[0].strip().split(" ")[0]
        if skill_name and not skill_name.startswith("("):
            print(f"     python skill_manager.py agents {skill_name}")
    print()


# ── Skill 医生 ─────────────────────────────────────────────────────

def cmd_doctor():
    """诊断所有 skill 的健康状态"""
    skills = discover_all_skills()
    print(f"\n{'='*60}")
    print(f"  Skill Doctor - 健康诊断")
    print(f"{'='*60}\n")

    issues = []
    ok_count = 0

    for s in skills:
        path = Path(s["path"])
        name = s["name"]

        # 检查 1: 文件/目录存在
        if not path.exists():
            issues.append({"skill": name, "root": s["root"], "issue": "路径不存在（死链接或已删除）", "severity": "error"})
            continue

        # 检查 2: 是否有 SKILL.md
        if s["has_skill_md"] and path.is_dir():
            skill_md = path / "SKILL.md"
            if not skill_md.exists():
                issues.append({"skill": name, "root": s["root"], "issue": "缺少 SKILL.md", "severity": "warn"})
                continue

            # 检查 3: SKILL.md 是否有必要的 frontmatter
            try:
                content = skill_md.read_text(encoding="utf-8", errors="replace")
                if not content.startswith("---"):
                    issues.append({"skill": name, "root": s["root"], "issue": "SKILL.md 缺少 YAML frontmatter", "severity": "warn"})
                else:
                    fm = content[3:content.find("---", 3)]
                    if "name:" not in fm:
                        issues.append({"skill": name, "root": s["root"], "issue": "SKILL.md frontmatter 缺少 name", "severity": "warn"})
                    if "description:" not in fm:
                        issues.append({"skill": name, "root": s["root"], "issue": "SKILL.md frontmatter 缺少 description", "severity": "warn"})
            except Exception:
                issues.append({"skill": name, "root": s["root"], "issue": "无法读取 SKILL.md", "severity": "error"})

        # 检查 4: 空目录
        if path.is_dir():
            contents = list(path.iterdir())
            if len(contents) <= 1 and path.name != "skill-manager":
                issues.append({"skill": name, "root": s["root"], "issue": "目录内容极少（可能不完整）", "severity": "info"})

        ok_count += 1

    # 输出结果
    if not issues:
        print(f"  ✅ 全部 {ok_count} 个 skill 健康！\n")
        return

    errs = [i for i in issues if i["severity"] == "error"]
    warns = [i for i in issues if i["severity"] == "warn"]
    infos = [i for i in issues if i["severity"] == "info"]

    if errs:
        print(f"  ❌ 错误 ({len(errs)}):")
        for e in errs:
            print(f"     {e['skill']} ({e['root']}): {e['issue']}")

    if warns:
        print(f"\n  ⚠️ 警告 ({len(warns)}):")
        for w in warns:
            print(f"     {w['skill']} ({w['root']}): {w['issue']}")

    if infos:
        print(f"\n  ℹ️ 提示 ({len(infos)}):")
        for i in infos:
            print(f"     {i['skill']} ({i['root']}): {i['issue']}")

    print(f"\n  ✅ 健康: {ok_count}  |  ⚠️ 警告: {len(warns)}  |  ❌ 错误: {len(errs)}")
    print(f"  运行 'python skill_manager.py update -y' 尝试修复\n")


# ── 多角度比较 ─────────────────────────────────────────────────────

COMPARE_GROUPS = {
    "论文审稿": {
        "desc": "从多个审稿视角评估论文",
        "skills": ["nature-reviewer", "academic-paper-reviewer"],
        "why": "nature-reviewer 偏 Nature/CNS 标准，academic-paper-reviewer 有 5 位分角色审稿人（EIC+方法论+领域+视角+魔鬼代言人），两者结合覆盖更全面",
    },
    "论文润色": {
        "desc": "多角度润色和降重",
        "skills": ["nature-polishing", "paper-spine-humanize"],
        "why": "nature-polishing 提升学术表达到 Nature 水准，paper-spine-humanize 专门降低 AIGC 检测率（支持知网/维普）",
    },
    "论文解析": {
        "desc": "深度阅读和理解论文",
        "skills": ["paper-analyzer", "nature-reader"],
        "why": "paper-analyzer 产出结构化 HTML 长文（6轮工作流+代码搜索），nature-reader 产出中英对照 Markdown reader（图文对应+全文翻译），互补使用",
    },
    "文献引用": {
        "desc": "构建引用支持库",
        "skills": ["nature-citation", "paper-spine-citation"],
        "why": "nature-citation 限定 Nature/CNS 系列期刊，paper-spine-citation 构建逐句 claim 级引用库（候选池 60 篇），覆盖不同层次",
    },
    "PPT/汇报": {
        "desc": "论文汇报材料",
        "skills": ["nature-paper2ppt", "paper-deck"],
        "why": "nature-paper2ppt 是中文文献汇报 PPTX，paper-deck 是高质感 AIGC 幻灯片（逐页生图），适用于不同场景",
    },
    "论文写作": {
        "desc": "从零写论文",
        "skills": ["nature-writing", "academic-paper", "paper-spine-rewrite"],
        "why": "nature-writing 偏 Nature 风格章节起草，academic-paper 是 12-agent 流水线，paper-spine-rewrite 基于动机+证据改写已有稿件",
    },
    "基金申请": {
        "desc": "NSFC 基金申请书",
        "skills": ["fund-background-writer", "fund-literature-review-writer",
                   "fund-research-content-writer", "fund-technical-route-writer"],
        "why": "四个 skill 分别覆盖：立项依据→文献综述→研究内容与科学问题→技术路线与创新特色",
    },
    "代码与复现": {
        "desc": "代码审查和可复现性",
        "skills": ["code-reviewer", "nature-academic-search"],
        "why": "code-reviewer 审查仿真代码质量，nature-academic-search 辅助查找开源实现和数据集",
    },
}


def cmd_compare(task: str = None):
    """多角度比较：同一任务用多个 skill，综合判断"""
    print(f"\n{'='*65}")
    print(f"  Skill Manager - 多角度交叉验证")
    print(f"{'='*65}")

    if not task:
        print(f"\n  可用的比较场景：\n")
        for name, cg in COMPARE_GROUPS.items():
            print(f"  📊 {name}")
            print(f"     {cg['desc']}")
            print(f"     Skill: {', '.join(cg['skills'][:3])}")
            print()
        print(f"  用法: python skill_manager.py compare \"论文审稿\"")
        print(f"  或直接说: \"帮我审这篇稿子，用多个 skill 交叉验证\"")
        return

    # 模糊匹配
    matched = None
    for name, cg in COMPARE_GROUPS.items():
        if task in name or name in task:
            matched = name
            break
    if not matched:
        # 关键词匹配
        for name in COMPARE_GROUPS:
            if any(kw in task for kw in name[:2]):
                matched = name
                break

    if not matched:
        print(f"\n  未匹配到场景。可用: {', '.join(COMPARE_GROUPS.keys())}")
        return

    cg = COMPARE_GROUPS[matched]
    print(f"\n  📊 场景: {matched}")
    print(f"  📝 {cg['desc']}")
    print(f"\n  {'='*55}")
    print(f"  💡 推荐同时使用以下 {len(cg['skills'])} 个 Skill：\n")

    for i, skill_name in enumerate(cg["skills"], 1):
        usage = SKILL_USAGE.get(skill_name, {})
        print(f"  [{i}] {skill_name}")
        print(f"      用法: {usage.get('how', '自然语言')}")
        print(f"      示例: {usage.get('example', '')}")
        if usage.get("note"):
            print(f"      备注: {usage['note']}")
        print()

    print(f"  {'='*55}")
    print(f"  🔬 为什么这样组合：")
    print(f"  {cg['why']}")
    print(f"\n  📋 建议操作流程：")
    print(f"  1. 先把任务发给第 1 个 skill，得到结果 A")
    print(f"  2. 再把同一个任务发给第 2 个 skill，得到结果 B")
    print(f"  3. 对比 A 和 B，取各自优点综合修改")
    if len(cg["skills"]) > 2:
        print(f"  4. 如有第 3 个 skill，重复上述步骤")
    print(f"  5. 综合所有意见后，发给 nature-polishing 最终润色")
    print()


# ── 一键导出配置 ──────────────────────────────────────────────────

def cmd_export(output_dir: str = None):
    """导出当前配置为一键安装脚本"""
    if not output_dir:
        output_dir = str(HOME / "skill-manager-export")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 收集所有已安装 skill 的来源
    unique_skills = {}
    for s in discover_all_skills():
        if s["name"] not in unique_skills and s["name"] != "skill-manager":
            unique_skills[s["name"]] = s

    # 分类
    npx_skills = []
    paperspine = False
    claude_plugin = False

    for name, s in sorted(unique_skills.items()):
        source = SKILL_SOURCES.get(name, {})
        if source.get("method") == "npx skills add":
            repo = source.get("repo", "")
            if repo and "nature-skills" in repo:
                npx_skills.append(("nature", repo, name))
            elif repo and "Chinese-Grant-Writer" in repo:
                npx_skills.append(("grant", repo, name))
            elif repo and "paper-craft-skills" in repo:
                npx_skills.append(("papercraft", repo, name))
            elif repo and "gemini-cli" in repo:
                npx_skills.append(("code", repo, name))
            elif repo and "trending-skills" in repo:
                npx_skills.append(("poster", repo, name))
            else:
                npx_skills.append(("other", repo, name))
        elif source.get("method") == "git clone + install.ps1":
            paperspine = True
        elif source.get("method") == "Claude Code plugin":
            claude_plugin = True

    # 生成 Windows PowerShell 脚本
    ps1_lines = [
        "# Skill Manager - 一键安装脚本",
        "# 生成时间: " + __import__('datetime').datetime.now().isoformat(),
        "# 用法: powershell -ExecutionPolicy Bypass -File install_all.ps1",
        "",
        "Write-Host '========================================' -ForegroundColor Cyan",
        "Write-Host '  Skill Manager - 一键安装 40 个科研 Skill' -ForegroundColor Cyan",
        "Write-Host '========================================' -ForegroundColor Cyan",
        "Write-Host ''",
        "",
        "# ===== 第 1 步: 安装 skill-manager 本身 =====",
        "Write-Host '[1/6] 安装 skill-manager...' -ForegroundColor Yellow",
    ]

    # skill-manager self-install
    ps1_lines.extend([
        "$managerDir = \"$env:USERPROFILE\\.agents\\skills\\skill-manager\"",
        "if (-not (Test-Path $managerDir)) {",
        "    Write-Host '  请先确保 skill-manager 已就位' -ForegroundColor Red",
        "    Write-Host '  git clone 本仓库后，复制 skill-manager 目录到 ~\\.agents\\skills\\' ",
        "}",
        "",
    ])

    # Group npx installs by repo
    repos = {}
    for cat, repo, name in npx_skills:
        if repo not in repos:
            repos[repo] = []
        repos[repo].append(name)

    step = 2
    for repo, names in repos.items():
        ps1_lines.append(f"# ===== 第 {step} 步 =====")
        ps1_lines.append(f"Write-Host '[{step}/6] 安装 {repo.split('/')[-1].replace('.git','')} ...' -ForegroundColor Yellow")
        for name in names:
            ps1_lines.append(f"Write-Host '  -> {name}' -ForegroundColor Gray")
        ps1_lines.append(f"npx.cmd skills add {repo} --skill '{' '.join(names)}' -y 2>&1 | Out-Null")
        ps1_lines.append(f"Write-Host '  完成!' -ForegroundColor Green")
        ps1_lines.append("")
        step += 1

    if paperspine:
        ps1_lines.extend([
            f"# ===== 第 {step} 步: PaperSpine =====",
            f"Write-Host '[{step}/6] 安装 PaperSpine...' -ForegroundColor Yellow",
            "if (-not (Test-Path $env:USERPROFILE\\PaperSpine)) {",
            "    git clone https://github.com/WUBING2023/PaperSpine.git $env:USERPROFILE\\PaperSpine 2>&1 | Out-Null",
            "}",
            "cd $env:USERPROFILE\\PaperSpine",
            "git pull 2>&1 | Out-Null",
            "powershell -ExecutionPolicy Bypass -File install.ps1 -Target all -CleanLegacy 2>&1 | Out-Null",
            "Write-Host '  完成!' -ForegroundColor Green",
            "",
        ])
        step += 1

    if claude_plugin:
        ps1_lines.extend([
            f"# ===== 第 {step} 步: Academic Research Skills (Claude Code 插件) =====",
            f"Write-Host '[{step}/6] Claude Code 插件需手动安装:' -ForegroundColor Yellow",
            "Write-Host '  在 Claude Code 中运行: /plugin install academic-research-skills@academic-research-skills' -ForegroundColor White",
            "",
        ])
        step += 1

    ps1_lines.extend([
        "# ===== 完成 =====",
        "Write-Host ''",
        "Write-Host '========================================' -ForegroundColor Green",
        "Write-Host '  全部安装完成!' -ForegroundColor Green",
        "Write-Host '  运行: python ~\\.agents\\skills\\skill-manager\\scripts\\skill_manager.py list' -ForegroundColor Green",
        "Write-Host '========================================' -ForegroundColor Green",
    ])

    install_ps1 = out / "install_all.ps1"
    install_ps1.write_text("\n".join(ps1_lines) + "\n", encoding="utf-8")

    # 复制 skill-manager 自身到导出目录
    manager_src = HOME / ".agents" / "skills" / "skill-manager"
    manager_dst = out / "skill-manager"
    if manager_src.exists():
        if manager_dst.exists():
            shutil.rmtree(manager_dst)
        shutil.copytree(manager_src, manager_dst)

    # 生成 setup.ps1（总入口：复制 manager + 运行安装）
    setup_lines = [
        "# Skill Manager - 总安装入口",
        "# 只需运行这一个脚本即可完成全部安装",
        "# 用法: powershell -ExecutionPolicy Bypass -File setup.ps1",
        "",
        '$root = $PSScriptRoot',
        "",
        "# Step 1: 安装 skill-manager 到本地",
        'Write-Host "========================================" -ForegroundColor Cyan',
        'Write-Host "  Step 1: 安装 Skill Manager 本身" -ForegroundColor Cyan',
        'Write-Host "========================================" -ForegroundColor Cyan',
        '$src = Join-Path $root "skill-manager"',
        'if (-not (Test-Path $src)) {',
        '    Write-Host "错误: 未找到 skill-manager 文件夹" -ForegroundColor Red',
        '    exit 1',
        '}',
        '$dst1 = "$env:USERPROFILE\\.agents\\skills\\skill-manager"',
        '$dst2 = "$env:USERPROFILE\\.claude\\skills\\skill-manager"',
        'New-Item -ItemType Directory -Force -Path (Split-Path $dst1) | Out-Null',
        'New-Item -ItemType Directory -Force -Path (Split-Path $dst2) | Out-Null',
        'Copy-Item -Recurse -Force $src $dst1',
        'Copy-Item -Recurse -Force $src $dst2 -ErrorAction SilentlyContinue',
        'Write-Host "  skill-manager 已安装" -ForegroundColor Green',
        "",
        "# Step 2: 运行批量安装",
        'Write-Host ""',
        'Write-Host "========================================" -ForegroundColor Cyan',
        'Write-Host "  Step 2: 安装 40 个科研 Skill" -ForegroundColor Cyan',
        'Write-Host "========================================" -ForegroundColor Cyan',
        '$installScript = Join-Path $root "install_all.ps1"',
        'if (Test-Path $installScript) {',
        '    & $installScript',
        '} else {',
        '    Write-Host "错误: 未找到 install_all.ps1" -ForegroundColor Red',
        '}',
        "",
        "# 完成",
        'Write-Host ""',
        'Write-Host "========================================" -ForegroundColor Green',
        'Write-Host "  全部完成！" -ForegroundColor Green',
        'Write-Host "  验证: python ~\\.agents\\skills\\skill-manager\\scripts\\skill_manager.py list" -ForegroundColor White',
        'Write-Host "========================================" -ForegroundColor Green',
    ]
    setup_ps1 = out / "setup.ps1"
    setup_ps1.write_text("\n".join(setup_lines) + "\n", encoding="utf-8")

    # 生成 JSON 配置快照
    snapshot = {
        "version": "1.0",
        "exported_at": __import__('datetime').datetime.now().isoformat(),
        "total_skills": len(unique_skills),
        "repos": {repo: names for repo, names in repos.items()},
        "has_paperspine": paperspine,
        "has_claude_plugin": claude_plugin,
        "skills_detail": {name: SKILL_SOURCES.get(name, {}) for name in sorted(unique_skills.keys())},
    }
    json_path = out / "skill_config.json"
    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  配置导出完成")
    print(f"{'='*60}")
    print(f"  📁 目录: {output_dir}")
    print(f"  📄 setup.ps1          — 🔥 总入口（同学只需跑这个）")
    print(f"  📄 install_all.ps1    — 批量安装脚本")
    print(f"  📄 skill_config.json  — 配置快照")
    print(f"  📁 skill-manager/     — Manager 自身")
    print(f"\n  🚀 同学使用方法：")
    print(f"  1. 把 {output_dir} 整个文件夹发给同学")
    print(f"  2. 同学右键 setup.ps1 → 用 PowerShell 运行")
    print(f"  3. 等待 5-10 分钟，全部自动完成")
    print(f"  4. 验证: python ~\\.agents\\skills\\skill-manager\\scripts\\skill_manager.py list")
    print()


# ── 交互式向导 ───────────────────────────────────────────────────

WIZARD_TEMPLATES = {
    "paper": {
        "label": "期刊/会议论文",
        "phases": [
            {"name": "信息收集", "skill": None, "template": """请告诉我以下信息：
1. 论文标题或研究方向（如：RIS辅助的ISAC系统波束赋形）
2. 目标期刊/会议（如：IEEE TWC / ICC 2026）
3. 你已经有哪些材料（实验数据、初稿、参考文献等）
4. 特殊要求（页数限制、格式要求等）
"""},
            {"name": "文献调研", "skill": "nature-academic-search + deep-research",
             "prompt": """请帮我调研 "{title}" 方向的文献：
1. 在 arXiv、IEEE Xplore、Google Scholar 上搜索近 3 年相关工作
2. 按以下维度分类：最相关方法(>=5篇)、经典baseline(>=3篇)、最新SOTA(>=3篇)
3. 总结现有方法的共同假设和局限性
4. 输出格式：每篇标注标题、作者、年份、核心贡献、与我工作的关系
"""},
            {"name": "创新点确认", "skill": "deep-research + academic-paper",
             "prompt": """基于文献调研，分析 "{title}" 的创新空间：
1. 现有方法的 3 个主要痛点是什么？
2. 我可以从哪些角度突破？（理论/算法/系统/应用）
3. 我的方法相比现有工作的核心差异是什么？
4. 用一句话表述核心贡献（contribution statement）
5. 这个贡献是否足够支撑 {venue}？不够的话怎么加强
"""},
            {"name": "初稿撰写", "skill": "nature-writing + academic-paper",
             "prompt": """请起草 "{title}" 的论文初稿，目标 {venue}。
结构：Abstract(<=200词) → Introduction(4-5段) → System Model → Proposed Method(配公式) → Simulation Results(表格+解读) → Conclusion
注意：IEEE学术风格，每个公式后跟人话解释，引用前面文献调研的论文
"""},
            {"name": "引用验证", "skill": "nature-citation",
             "prompt": """验证 "{title}" 初稿中所有引用：逐一检查DOI真实性、为每个claim找支撑文献、检查格式符合{venue}要求、标记存疑引用
"""},
            {"name": "模拟审稿", "skill": "nature-reviewer + academic-paper-reviewer",
             "prompt": """以 {venue} 审稿人视角审查 "{title}"：模拟3位审稿人(领域专家/方法学/跨学科)，评估新颖性/技术深度/实验充分性/写作质量，列出Major Issues和Minor Issues
"""},
            {"name": "修改完善", "skill": "paper-spine-rewrite + nature-polishing",
             "prompt": """根据审稿意见修改 "{title}"：逐条回复审稿意见、修改正文对应段落、润色至期刊水准、用paper-spine-humanize降AIGC率
"""},
            {"name": "图表升级", "skill": "nature-figure",
             "prompt": """检查升级 "{title}" 图表：分辨率>=600dpi、统一字体(Arial>=8pt)、色彩对色盲友好、图注完整(统计量/样本量/误差线)、重绘为矢量图
"""},
            {"name": "最终输出", "skill": "paper-spine-latex + paper-spine-audit",
             "prompt": """生成 "{title}" 最终版：组装LaTeX({venue}模板)、编译PDF、审计完整性、生成Data Availability Statement、可选Word版
"""},
        ]
    },
    "patent": {
        "label": "发明专利",
        "phases": [
            {"name": "信息收集", "skill": None, "template": """请告诉我以下信息：
1. 发明名称（如：一种基于深度学习的信道估计方法）
2. 技术领域
3. 该发明解决了什么技术问题
4. 已有的相关资料（论文、技术报告等）
"""},
            {"name": "现有技术检索", "skill": "nature-academic-search + deep-research",
             "prompt": """检索 "{title}" 的现有技术：搜索专利数据库和学术论文、分析现有技术不足、明确区别技术特征、总结技术问题和有益效果
"""},
            {"name": "专利撰写", "skill": "nature-paper-to-patent",
             "prompt": """根据 "{title}" 撰写中国发明专利：权利要求书(独立+从属)、说明书(技术领域/背景/发明内容/附图说明/实施方式)、摘要+摘要附图、确保每个特征有实施例支撑
"""},
            {"name": "审查与修改", "skill": "nature-reviewer",
             "prompt": """审查 "{title}" 专利：新颖性(与现有技术实质性区别)、创造性(突出特点和显著进步)、实用性(能否制造使用)、权利要求是否清楚简要、说明书是否充分公开
"""},
            {"name": "最终输出", "skill": None,
             "prompt": """生成 "{title}" 专利最终版：权利要求书.docx、说明书.docx、摘要.docx、摘要附图.png、发明专利请求书
"""},
        ]
    },
    "grant": {
        "label": "基金申请",
        "phases": [
            {"name": "信息收集", "skill": None, "template": """请告诉我以下信息：
1. 基金类型（国自然面上/青年/重点 / 博士创新基金 / 省基金）
2. 项目名称
3. 研究领域
4. 预算范围
5. 已有的研究基础（论文、专利、前期工作）
"""},
            {"name": "立项依据", "skill": "fund-background-writer + fund-literature-review-writer",
             "prompt": """准备 "{title}" 的立项依据：研究背景与意义(国家需求/科学前沿)、国内外研究现状(
近3年综述)、现有不足与切入点、参考文献(>=20篇,80%近3年)
"""},
            {"name": "研究方案", "skill": "fund-research-content-writer + researchwrite",
             "prompt": """撰写 "{title}" 研究方案：研究目标(1-2总目标+3-4具体目标)、研究内容(3-4方面)、
技术路线(Mermaid流程图)、关键科学问题(2-3个)、创新点(3-4个)、可行性分析
"""},
            {"name": "研究计划", "skill": "fund-technical-route-writer",
             "prompt": """制定 "{title}" 研究计划：年度研究计划(分年度内容与目标)、预期成果(论文3-5篇/
专利1-2项)、研究进度甘特图、经费预算说明
"""},
            {"name": "审阅与润色", "skill": "nature-polishing + nature-reviewer",
             "prompt": """审阅 "{title}" 基金申请书：逻辑是否清晰(问题->目标->内容->方法->成果)、创新点是否突出、方案是否可行、文字是否精炼、格式是否符合要求
"""},
        ]
    },
}


def cmd_wizard(wiz_type: str = None):
    """交互式向导：选题 -> 搜索 -> 写稿 -> 审稿 -> 修改 -> 输出"""
    print(f"\n{'='*65}")
    print(f"  Skill Manager - 项目向导")
    print(f"{'='*65}")

    if not wiz_type:
        print(f"\n  请选择项目类型：")
        for key, tmpl in WIZARD_TEMPLATES.items():
            print(f"    {key:<8} - {tmpl['label']}")
        print(f"\n  用法: python skill_manager.py wizard <paper|patent|grant>")
        return

    if wiz_type not in WIZARD_TEMPLATES:
        print(f"  未知: {wiz_type}。可选: {', '.join(WIZARD_TEMPLATES.keys())}")
        return

    tmpl = WIZARD_TEMPLATES[wiz_type]
    phases = tmpl["phases"]
    print(f"\n  {tmpl['label']} | {len(phases)} 步完成")
    print(f"  {'='*60}")

    for i, phase in enumerate(phases, 1):
        icon = "📋" if "template" in phase else "▶️"
        print(f"\n  [{icon} Step {i}/{len(phases)}] {phase['name']}")
        if phase["skill"]:
            print(f"   Skill: {phase['skill']}")
        if "template" in phase:
            for line in phase["template"].strip().split("\n"):
                print(f"   {line}")
        elif "prompt" in phase:
            print(f"   复制发给 AI agent:")
            print(f"   {'─'*50}")
            for line in phase["prompt"].strip().split("\n"):
                print(f"   {line}")
            print(f"   {'─'*50}")

    # 保存工作流文件
    output_path = HOME / f"wizard_{wiz_type}_workflow.md"
    lines = [f"# {tmpl['label']} 工作流\n\n"]
    lines.append("> 使用前请替换 {title} 和 {venue} 为你的实际信息\n\n")
    for i, phase in enumerate(phases, 1):
        lines.append(f"## Step {i}: {phase['name']}\n\n")
        if phase["skill"]:
            lines.append(f"**Skill**: {phase['skill']}\n\n")
        if "prompt" in phase:
            lines.append(phase["prompt"].strip() + "\n\n")
        elif "template" in phase:
            lines.append("```\n" + phase["template"].strip() + "\n```\n\n")
    output_path.write_text("".join(lines), encoding="utf-8")
    print(f"\n  工作流已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Skill Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all skills").add_argument(
        "--json", action="store_true", help="JSON output"
    )

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

    info = sub.add_parser("info", help="Show detailed info about a skill (what it does, how to use)")
    info.add_argument("name", nargs="?", help="Skill name (or part of name)")

    sub.add_parser("usage", help="Quick reference: how to invoke each skill")

    upd = sub.add_parser("update", help="Update all installed skills to latest")
    upd.add_argument("--all", action="store_true", help="Update all (default)")
    upd.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    srch = sub.add_parser("search", help="Search GitHub/skills.sh for new skills")
    srch.add_argument("keyword", help="Search keyword")

    inst = sub.add_parser("install", help="Install a skill from GitHub (owner/repo)")
    inst.add_argument("source", help="GitHub repo (owner/repo or full URL)")
    inst.add_argument("--skill", dest="skill_name", help="Specific skill name in the repo")
    inst.add_argument("--yes", "-y", action="store_true")

    ag = sub.add_parser("agents", help="List all agents inside a skill")
    ag.add_argument("name", nargs="?", help="Skill name (e.g., academic-paper-reviewer)")

    adv = sub.add_parser("advise", help="Get a step-by-step workflow recommendation")
    adv.add_argument("query", nargs="?", help="Describe what you need (e.g., \"I have a draft, want to publish\")")

    wiz = sub.add_parser("wizard", help="Interactive project wizard (paper/patent/grant)")
    wiz.add_argument("type", nargs="?", choices=["paper", "patent", "grant"],
                     help="Project type: paper, patent, or grant")

    sub.add_parser("doctor", help="Diagnose all skills for issues (missing files, bad frontmatter)")

    comp = sub.add_parser("compare", help="Compare multiple skills for the same task (cross-validation)")
    comp.add_argument("task", nargs="?", help="Task to compare (e.g., 'review', 'polish', 'parse')")

    exp = sub.add_parser("export", help="Export current config as one-click install script")
    exp.add_argument("output", nargs="?", help="Output directory (default: ~/skill-manager-export)")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(json_output=getattr(args, "json", False))
    elif args.command == "remove":
        cmd_remove(args.name, from_root=getattr(args, "from_root", None), yes=args.yes)
    elif args.command == "where":
        cmd_where(args.name)
    elif args.command == "sync":
        cmd_sync(args.src, args.dst, yes=args.yes)
    elif args.command == "info":
        if args.name:
            cmd_info(args.name)
        else:
            print("Usage: skill_manager.py info <skill-name>")
    elif args.command == "usage":
        cmd_usage()
    elif args.command == "update":
        cmd_update(yes=args.yes)
    elif args.command == "search":
        cmd_search(args.keyword)
    elif args.command == "install":
        cmd_install(args.source, skill_name=getattr(args, "skill_name", None), yes=args.yes)
    elif args.command == "agents":
        cmd_agents(args.name)
    elif args.command == "advise":
        cmd_advise(args.query)
    elif args.command == "wizard":
        cmd_wizard(args.type)
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "compare":
        cmd_compare(args.task)
    elif args.command == "export":
        cmd_export(args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
