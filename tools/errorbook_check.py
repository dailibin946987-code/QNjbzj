#!/usr/bin/env python3
"""QNjbzj 错题本断言执行器。

读取 data/errorbook/*.json 用例（或内置 E-01~E-14 简化版），对目标文本执行断言：
- keywords：命中关键词即触发该错题检查
- forbidden：若命中关键词且文本违反规则（required 未出现 / banned 出现），判 FAIL
输出 JSON 报告，供回归/监察使用。

用例格式（json）：
[{"id": "E-02", "keywords": ["回来", "替我"], "required": [], "banned": ["你回来"]}]

用法：
    python errorbook_check.py check "台词文本" [--cases data/errorbook/e01-e14.json]
    python errorbook_check.py demo
"""
import argparse
import json
import os
import sys

BUILTIN_CASES = [
    {"id": "E-01", "keywords": ["临终", "遗言", "口型"], "required": [], "banned": [], "note": "检查语义方向"},
    {"id": "E-02", "keywords": ["回来", "替我", "承诺"], "required": [], "banned": [], "note": "承诺已在前场景完成应整句删除"},
    {"id": "E-03", "keywords": ["再说一遍", "重复"], "required": [], "banned": [], "note": "已说过台词直接删除"},
    {"id": "E-04", "keywords": ["红绳", "红线", "道具"], "required": [], "banned": [], "note": "道具同一性/断裂须有行为交代"},
    {"id": "E-05", "keywords": ["拿出", "掏出一根", "从包里"], "required": [], "banned": [], "note": "关键道具须有来源交代"},
    {"id": "E-06", "keywords": ["设定里", "设定说"], "required": [], "banned": [], "note": "设定须在场景真实落点"},
    {"id": "E-07", "keywords": ["消失", "不见了"], "required": [], "banned": [], "note": "角色退出须有交代"},
    {"id": "E-08", "keywords": ["你回来", "你走", "你回不来"], "required": [], "banned": [], "note": "动作已完成时勿替动作说结论"},
    {"id": "E-09", "keywords": ["三生三世", "前世", "命中注定"], "required": [], "banned": [], "note": "观察->发现->感受->判断递进"},
    {"id": "E-10", "keywords": ["打结三遍", "打了三个结", "结了三道"], "required": [], "banned": [], "note": "特殊动作须有前因交代"},
    {"id": "E-11", "keywords": ["回来", "出海", "留学", "等你"], "required": [], "banned": [], "note": "主语须清晰"},
    {"id": "E-12", "keywords": ["攥在", "系着", "摘下"], "required": [], "banned": [], "note": "状态过渡须有行为"},
    {"id": "E-13", "keywords": ["外婆说过", "祖上", "预言", "命中注定"], "required": [], "banned": [], "note": "无关家族无相同预言"},
    {"id": "E-14", "keywords": ["没人知道", "殊不知", "原来", "舍不得扔", "假笑", "金句", "全城"], "required": [], "banned": [], "note": "AI 味病句/作者腔：白描缺失，见 references/14_plain_descriptive_writing.md"},
]


def load_cases(path):
    if not os.path.exists(path):
        return BUILTIN_CASES
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check(text, cases):
    results = []
    text_l = text.lower()
    for c in cases:
        hit = any(k.lower() in text_l for k in c.get("keywords", []))
        if not hit:
            continue
        banned = [b for b in c.get("banned", []) if b.lower() in text_l]
        missing = [r for r in c.get("required", []) if r.lower() not in text_l]
        ok = (not banned) and (not missing)
        results.append({
            "id": c["id"], "hit": True, "pass": ok,
            "banned_found": banned, "required_missing": missing,
            "note": c.get("note", ""),
        })
    return results


def main():
    ap = argparse.ArgumentParser(description="QNjbzj errorbook assertion runner")
    ap.add_argument("cmd", choices=["check", "demo"])
    ap.add_argument("text", nargs="?", default="", help="待检文本")
    ap.add_argument("--cases", default="")
    args = ap.parse_args()

    if args.cmd == "demo":
        demo_text = "她把绳系回腕上，又说了一遍：'你回来，我替你带着。'"
        res = check(demo_text, load_cases(args.cases))
        print(json.dumps({"pass": all(r["pass"] for r in res), "results": res}, ensure_ascii=False, indent=2))
        return

    if not args.text:
        print("请提供待检文本")
        sys.exit(1)
    res = check(args.text, load_cases(args.cases))
    report = {"pass": all(r["pass"] for r in res), "results": res}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
