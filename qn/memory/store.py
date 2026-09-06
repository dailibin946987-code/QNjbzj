"""只增记忆存储：errors / validated / reference 分区，只追加不覆盖。

对接 skill-evo-team 主脑"技能只存知识、不存项目；记忆只能增加，不能迭代"。
经验从 errors(只增) -> validated(反复验证) -> anchors(锚定不可变) 的单向流动。
"""
import json
import os
import time

DATA_DIR = r"D:\D_AIdirector\QNjbzj\data"
ERROR_DIR = os.path.join(DATA_DIR, "errors")


class AppendOnlyStore:
    """按分区(append-only log) 存储记忆条目。

    分区约定：
      errors     -> data/errors/          错误/失败经验（只增）
      validated  -> data/validated/       反复验证有效的技巧
      reference  -> data/reference/       通用参考知识
    每条记录 {id, ts, kind, content, source, confidence}，永不删除覆盖。
    """

    def __init__(self, base=DATA_DIR):
        self.base = base
        for part in ("errors", "validated", "reference"):
            os.makedirs(os.path.join(base, part), exist_ok=True)

    def append(self, partition, entry):
        assert partition in ("errors", "validated", "reference"), partition
        entry = dict(entry)
        entry.setdefault("id", "%s-%d" % (partition, int(time.time() * 1000)))
        entry.setdefault("ts", time.time())
        fp = os.path.join(self.base, partition, entry["id"] + ".json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        return entry["id"]

    def list_partition(self, partition):
        fp = os.path.join(self.base, partition)
        out = []
        if os.path.isdir(fp):
            for fn in sorted(os.listdir(fp)):
                if fn.endswith(".json"):
                    with open(os.path.join(fp, fn), encoding="utf-8") as f:
                        out.append(json.load(f))
        return out

    def promote(self, entry_id):
        """errors -> validated 单向晋升（原记录保留，只新增 validated 副本）。"""
        for src in self.list_partition("errors"):
            if src.get("id") == entry_id:
                return self.append("validated", {**src, "promoted_from": entry_id})
        return None


# 便捷日志落点：data/logs/append.log（只增）
def log_event(stream, payload):
    fp = os.path.join(DATA_DIR, "logs", "%s.log" % stream)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **payload}, ensure_ascii=False) + "\n")
