"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
示例数据支持一键重置：reset() 会把所有表恢复成种子数据的初始状态。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.seed import SEED_ROWS


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {}
        self.seeded_at = ""
        self.resets = 0
        self.reset()

    def reset(self) -> None:
        """把所有模块的数据恢复成种子初始状态；被改脏的数据一键还原。"""
        self._tables.clear()
        for name, rows in SEED_ROWS.items():
            self._tables[name] = [dict(row) for row in rows]
        self.seeded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.resets += 1

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def seed_status(self) -> dict[str, Any]:
        """示例数据状态：模块数、总行数、是否仍与种子一致、最近一次重建时间。"""
        pristine = all(
            self._tables.get(name) == [dict(row) for row in rows]
            for name, rows in SEED_ROWS.items()
        )
        return {
            "modules": len(self._tables),
            "rows": sum(len(rows) for rows in self._tables.values()),
            "pristine": pristine,
            "seeded_at": self.seeded_at,
            "resets": self.resets,
        }

    def overview(self) -> dict[str, object]:
        modules: list[dict[str, object]] = []
        for name in self.module_names():
            rows = self.rows(name)
            modules.append({
                "name": name,
                "created": len(rows),
                "pending": sum(1 for row in rows if row.get("pending")),
                "abnormal": sum(1 for row in rows if row.get("abnormal")),
            })
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}


store = Store()
