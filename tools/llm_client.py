#!/usr/bin/env python3
"""QNjbzj LLM 客户端（OpenAI 兼容）。默认连本地 Ollama；可配任意 OpenAI 兼容端点。

用法（local-llm 模式）：
    python llm_client.py chat "写一句离别台词" [--model qwen2.5:14b]
    python llm_client.py --base-url http://127.0.0.1:11434/v1 --api-key ollama chat "..."

作为库：
    from llm_client import LLMClient
    c = LLMClient(base_url="http://127.0.0.1:11434/v1", model="qwen2.5:14b")
    print(c.chat("...", system="你是全能剧本专家主笔"))
"""
import argparse
import json
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL = "qwen2.5:14b"


class LLMClient:
    def __init__(self, base_url=DEFAULT_BASE, api_key="", model=DEFAULT_MODEL, timeout=120):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _post(self, path, payload):
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     **({"Authorization": "Bearer " + self.api_key} if self.api_key else {})},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def chat(self, user, system=None, temperature=0.7, max_tokens=None):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        payload = {"model": self.model, "messages": messages, "stream": False, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        data = self._post("/chat/completions", payload)
        return data["choices"][0]["message"]["content"].strip()

    def embed(self, text, model=None):
        """返回向量列表；用于记忆检索（需本机有 embedding 模型）。"""
        payload = {"model": model or "nomic-embed-text", "input": text}
        data = self._post("/embeddings", payload)
        return data["data"][0]["embedding"]

    def health(self):
        try:
            self._post("/models", {}) if False else None
            return False
        except Exception:
            return False


def _probe(base_url):
    """探测端点是否可达（GET /models）。"""
    try:
        with urllib.request.urlopen(base_url + "/models", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("id") or m.get("name") for m in data.get("data", [])]
            return True, models
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser(description="QNjbzj LLM client (OpenAI compatible)")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--api-key", default="")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--list", action="store_true", help="列出可用模型")
    ap.add_argument("cmd", nargs="?", choices=["chat", "embed"], help="命令")
    ap.add_argument("text", nargs="?", help="输入文本")
    ap.add_argument("--system", default="", help="system prompt")
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    if args.list:
        ok, info = _probe(args.base_url)
        print(("可达，模型: " if ok else "不可达: ") + str(info))
        return
    if args.cmd == "chat" and args.text:
        c = LLMClient(args.base_url, args.api_key, args.model)
        print(c.chat(args.text, system=args.system, temperature=args.temperature))
    elif args.cmd == "embed" and args.text:
        c = LLMClient(args.base_url, args.api_key)
        v = c.embed(args.text)
        print(f"embedding dim={len(v)}")
    else:
        ok, info = _probe(args.base_url)
        print(("Ollama 可达，模型: " if ok else "端点不可达: ") + str(info))


if __name__ == "__main__":
    main()
