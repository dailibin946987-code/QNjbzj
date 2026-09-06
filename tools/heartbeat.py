#!/usr/bin/env python3
"""QNjbzj 心跳自检脚本（保守保洁，只增不删）。

按心跳协议扫描记忆目录在 last_reviewed_change_at 后的变更，输出心跳状态。
绝不删除/覆盖内容；仅更新 state 文件。

用法：
    python heartbeat.py [--memory-root ../data/memory] [--state ../data/logs/heartbeat-state.json]
"""
import argparse
import json
import os
import time

DEFAULT_MEMORY_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "memory")
DEFAULT_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "logs", "heartbeat-state.json")


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _load_state(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _scan_changes(memory_root, since_ts):
    changed = []
    if not os.path.isdir(memory_root):
        return changed
    for layer in ("hot", "warm", "cold", "permanent"):
        d = os.path.join(memory_root, layer)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                mt = os.path.getmtime(p)
                if mt > since_ts:
                    changed.append(os.path.relpath(p, os.path.dirname(memory_root)))
    return changed


def run(memory_root, state_path):
    state = _load_state(state_path)
    state["last_heartbeat_started_at"] = _now_iso()
    last_reviewed = state.get("last_reviewed_change_at_ts", 0.0)
    changed = _scan_changes(memory_root, last_reviewed)

    if not changed:
        state["last_heartbeat_result"] = "HEARTBEAT_OK"
        state["last_actions"] = "no material change"
    else:
        # 保守整理：只建立索引摘要，不移动不删除内容
        state["last_heartbeat_result"] = "HEARTBEAT_REVIEWED"
        state["last_actions"] = f"发现 {len(changed)} 处变更文件，已建立变更清单（未改写内容）"
        state["changed_files"] = changed[:50]
        state["last_reviewed_change_at_ts"] = time.time()

    _save_state(state_path, state)
    print(f"[{state['last_heartbeat_result']}] {state['last_actions']}")
    if changed:
        for c in changed[:20]:
            print("  - " + c)
    return 0


def main():
    ap = argparse.ArgumentParser(description="QNjbzj heartbeat self-check")
    ap.add_argument("--memory-root", default=DEFAULT_MEMORY_ROOT)
    ap.add_argument("--state", default=DEFAULT_STATE)
    args = ap.parse_args()
    run(args.memory_root, args.state)


if __name__ == "__main__":
    main()
