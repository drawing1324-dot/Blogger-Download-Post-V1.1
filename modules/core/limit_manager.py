"""Simple per-blog post limiter for V1.1."""
import json
from pathlib import Path
from datetime import datetime


class LimitManager:
    def __init__(self, file="storage/post_limit.json"):
        self.file = Path(file)
        self.file.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.file.exists():
            return {"date": datetime.now().strftime("%Y-%m-%d"), "blogs": {}}
        with open(self.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "blogs" not in data:
            data = {"date": data.get("date", datetime.now().strftime("%Y-%m-%d")), "blogs": {"_legacy": data.get("count", 0)}}
        return data

    def can_post(self, limit, blog_id=None):
        data = self.load()
        today = datetime.now().strftime("%Y-%m-%d")
        if data.get("date") != today:
            return True
        key = str(blog_id) if blog_id is not None else "_legacy"
        return int(data.get("blogs", {}).get(key, 0)) < limit

    def increase(self, blog_id=None):
        data = self.load()
        today = datetime.now().strftime("%Y-%m-%d")
        if data.get("date") != today:
            data = {"date": today, "blogs": {}}
        key = str(blog_id) if blog_id is not None else "_legacy"
        data.setdefault("blogs", {})[key] = int(data["blogs"].get(key, 0)) + 1
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
