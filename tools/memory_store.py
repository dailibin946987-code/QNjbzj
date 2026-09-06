#!/usr/bin/env python3
"""QNjbzj 只增记忆存储（append-only + 检索）。

四层池：hot/warm/cold/permanent。铁律：只追加，不删除不覆盖。
可选 embedding 检索（连接本机 Ollama nomic-embed-text）。

用法：
    python memory_store.py add permanent anchors "P001|覆盖规则|示例" --note 来源
    python memory_store.py search "红绳道具" --top 3
"""
import argparse
import json
import os
import sys
import time
import urllib.request

DEFAULT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "memory")
LAYERS = ("hot", "warm", "cold", "permanent")
OLLAMA_URL = "http://127.0.0.1:11434/v1/embeddings"
EMBED_MODEL = "nomic-embed-text"


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _layer_dir(root, layer):
    d = os.path.join(root, layer)
    os.makedirs(d, exist_ok=True)
    return d


def _file(root, layer):
    return os.path.join(_layer_dir(root, layer), "entries.jsonl")


def add(root, layer, entry_type, content, source="", note=""):
    assert layer in LAYERS, f"layer must be in {LAYERS}"
    rec = {
        "id": f"{layer}-{int(time.time()*1000)}",
        "type": entry_type,
        "content": content,
        "source": source,
        "note": note,
        "created_at": _now(),
        "status": "tentative",
        "reuse_count": 0,
        "confidence": 0.5,
    }
    path = _file(root, layer)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec["id"]


def _read_all(root):
    out = []
    for layer in LAYERS:
        p = _file(root, layer)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    rec["_layer"] = layer
                    out.append(rec)
                except json.JSONDecodeError:
                    continue
    return out


def _embed(text):
    payload = json.dumps({"model": EMBED_MODEL, "input": text}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["data"][0]["embedding"]
    except Exception:
        return None


def _cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def search(root, query, top=3):
    recs = _read_all(root)
    if not recs:
        return []
    vec = _embed(query)
    if vec:
        for r in recs:
            r["_score"] = _cosine(vec, _embed(r.get("content", "")))
    else:
        # 无 embedding 时退化为关键词命中
        q = query.lower()
        for r in recs:
            content = (r.get("content", "") + " " + r.get("note", "")).lower()
            r["_score"] = 1.0 if q in content else 0.0
    recs.sort(key=lambda x: x["_score"], reverse=True)
    return [r for r in recs[:top] if r["_score"] > 0]


def main():
    ap = argparse.ArgumentParser(description="QNjbzj append-only memory store")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("layer", choices=LAYERS)
    a.add_argument("type", help="entry type: failure_pattern/user_preference/success_recipe/..."
                                "或 anchors/core_principles 等")
    a.add_argument("content", help="entry content")
    a.add_argument("--source", default="")
    a.add_argument("--note", default="")

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--top", type=int, default=3)

    args = ap.parse_args()
    if args.cmd == "add":
        rid = add(args.root, args.layer, args.type, args.content, args.source, args.note)
        print(f"已追加: {rid} -> {args.layer}/{args.type}")
    elif args.cmd == "search":
        for r in search(args.root, args.query, args.top):
            print(f"[{r['_layer']}] {r['id']} | {r['type']} | score={r['_score']:.3f} | {r['content'][:80]}")


if __name__ == "__main__":
    main()
