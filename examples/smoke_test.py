#!/usr/bin/env python3
"""QNjbzj 端到端冒烟测试：结构完整性 + 工具可运行性 + 可选 LLM 探测。

用法：
    python examples/smoke_test.py [--llm-probe]
退出码：0 全过 / 1 有失败
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skill")

REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "agents/director-agent.md", "agents/script-agent.md", "agents/monitor-agent.md",
    "agents/memory-agent.md", "agents/evolution-agent.md", "agents/heartbeat-agent.md",
    "references/00_overview.md", "references/01_ly_jbkf_workflow.md",
    "references/02_six_gates_aesthetics.md", "references/03_dialogue_engine.md",
    "references/04_errorbook.md", "references/05_memory_protocol.md",
    "references/06_heartbeat_protocol.md", "references/07_evolution_protocol.md",
    "references/08_review_dimensions.md", "references/09_style_modules.md",
    "references/10_story_structure.md", "references/11_visual_language.md",
    "references/12_character_dialogue.md", "references/13_genre_grammar.md",
    "references/14_plain_descriptive_writing.md",
    "templates/screenplay-format.md", "templates/review-report.md",
    "templates/regression-report.md",
]

REQUIRED_TOOLS = ["llm_client.py", "memory_store.py", "errorbook_check.py", "heartbeat.py"]


def check_structure():
    missing = []
    for rel in REQUIRED_SKILL_FILES:
        if not os.path.exists(os.path.join(SKILL_DIR, rel)):
            missing.append("skill/" + rel)
    for rel in REQUIRED_TOOLS:
        if not os.path.exists(os.path.join(ROOT, "tools", rel)):
            missing.append("tools/" + rel)
    return missing


def run_tool_checks():
    failures = []
    # errorbook_check demo
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "errorbook_check.py"), "demo"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    if p.returncode != 0:
        failures.append("errorbook_check demo 失败: " + p.stderr[-300:])
    # heartbeat
    state = os.path.join(ROOT, "data", "logs", "smoke-heartbeat-state.json")
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "heartbeat.py"),
                        "--state", state], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    if p.returncode != 0 or "HEARTBEAT" not in p.stdout:
        failures.append("heartbeat 失败: " + p.stdout[-200:] + p.stderr[-200:])
    # memory add + search（无 embedding 自动退化关键词）
    mem_root = os.path.join(ROOT, "data", "memory")
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "memory_store.py"),
                        "--root", mem_root, "add", "warm", "smoke_test", "冒烟测试条目 红绳 离别 台词"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    if p.returncode != 0:
        failures.append("memory add 失败: " + p.stderr[-300:])
    else:
        p2 = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "memory_store.py"),
                             "--root", mem_root, "search", "红绳 离别", "--top", "1"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if p2.returncode != 0 or "smoke_test" not in p2.stdout:
            failures.append("memory search 失败: " + p2.stdout[-200:] + p2.stderr[-200:])
    return failures


def llm_probe():
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        from llm_client import _probe  # noqa
        ok, info = _probe("http://127.0.0.1:11434/v1")
        return ok, info
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-probe", action="store_true", help="探测本地 Ollama 是否可达")
    args = ap.parse_args()

    results = []
    missing = check_structure()
    results.append(("结构完整性", len(missing) == 0,
                    "缺失: " + ", ".join(missing) if missing else f"{len(REQUIRED_SKILL_FILES)} 知识文件 + {len(REQUIRED_TOOLS)} 工具 全齐"))

    if not missing:
        fails = run_tool_checks()
        results.append(("工具冒烟（错题断言/心跳/记忆）", len(fails) == 0,
                        "; ".join(fails) if fails else "errorbook_check demo 通过 / heartbeat OK / memory 追加+检索 OK"))

    if args.llm_probe:
        ok, info = llm_probe()
        results.append(("本地 LLM（Ollama 11434）", ok, str(info)))

    print("=== QNjbzj 冒烟测试报告 ===")
    all_ok = True
    for name, ok, detail in results:
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print("=== 结论: " + ("全部通过" if all_ok else "存在失败项") + " ===")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
