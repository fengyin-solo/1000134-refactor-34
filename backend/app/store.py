"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
示例数据不再在构造时自动灌入，而由启动流程统一调用 reset_seed() 装载，这样：
- 启动自检与重置入口走的是同一份装载逻辑；
- 示例数据被改脏（增删改、清空）后，可以随时 reset_seed() 恢复成初始状态。
"""
from __future__ import annotations

import copy
from typing import Any

from app.seed import SEED_ROWS

# 示例数据状态：与种子一致 / 已被改动 / 尚未装载（表全空且种子非空）
SEED_PRISTINE = "pristine"
SEED_DIRTY = "dirty"
SEED_EMPTY = "empty"


class Store:
    def __init__(self) -> None:
        # 预置全部模块的空表，保证模块数量始终稳定，数据由 reset_seed() 灌入。
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [] for name in SEED_ROWS
        }

    def reset_seed(self) -> dict[str, int]:
        """丢弃当前全部数据，重新装载一份未被改动的示例数据。

        返回每个模块装载后的记录数，供启动日志与重置接口使用。
        """
        counts: dict[str, int] = {}
        for name in sorted(SEED_ROWS):
            rows = copy.deepcopy(SEED_ROWS[name])
            self._tables[name] = rows
            counts[name] = len(rows)
        # 启动过程中如果出现过种子之外的模块，也一并清掉。
        for name in [name for name in self._tables if name not in SEED_ROWS]:
            del self._tables[name]
        return counts

    def seed_status(self) -> dict[str, object]:
        """对照种子数据检查当前示例数据的状态。"""
        modules = self.module_names()
        total_rows = sum(len(self._tables[name]) for name in modules)
        seed_total = sum(len(SEED_ROWS.get(name, [])) for name in modules)

        if total_rows == 0 and seed_total > 0:
            state = SEED_EMPTY
        elif self._matches_seed():
            state = SEED_PRISTINE
        else:
            state = SEED_DIRTY

        return {
            "state": state,
            "modules": len(modules),
            "rows": total_rows,
            "seed_rows": seed_total,
        }

    def _matches_seed(self) -> bool:
        if set(self._tables) != set(SEED_ROWS):
            return False
        for name, seed_rows in SEED_ROWS.items():
            current = self._tables[name]
            if len(current) != len(seed_rows):
                return False
            for row, seed_row in zip(current, seed_rows):
                if row != seed_row:
                    return False
        return True

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

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
