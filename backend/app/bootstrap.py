"""共用启动流程：读取运行环境、校验配置、装载示例数据并输出自检结果。

启动时（FastAPI lifespan）与健康检查接口共用这里的 run_self_check()，
保证「容器重启后接口里看到的自检结果」和「启动日志里打印的」来自同一份口径；
重置示例数据的入口也复用 store.reset_seed() 后再跑一次同一套自检。
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app.routers import ROUTERS
from app.store import SEED_PRISTINE, store

logger = logging.getLogger("app.bootstrap")
if not logger.handlers:
    # uvicorn 默认只配置自己的 logger，这里给应用日志挂一个独立 handler，
    # 保证无论以什么方式启动（uvicorn / 容器 CMD）自检日志都能稳定打到 stdout。
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def run_self_check(settings: Settings) -> dict[str, Any]:
    """执行一次启动自检：模块注册情况 + 示例数据状态。

    启动日志与 GET /api/health 共用本函数，二者结果永远一致。
    """
    registered = {module.__name__.rsplit(".", 1)[-1] for module in ROUTERS}
    data_modules = set(store.module_names())
    missing = sorted(registered - data_modules)
    extra = sorted(data_modules - registered)

    seed = store.seed_status()
    ok = not missing and not extra and seed["state"] == SEED_PRISTINE
    return {
        "ok": ok,
        "env": settings.env,
        "modules": len(data_modules),
        "registered_routers": len(registered),
        "missing_modules": missing,
        "extra_modules": extra,
        "seed": seed,
    }


def format_self_check(report: dict[str, Any]) -> str:
    """把自检结果格式化成启动日志里的一行可读摘要。"""
    seed = report["seed"]
    state_text = {
        "pristine": "与种子一致",
        "dirty": "已被改动",
        "empty": "尚未装载",
    }.get(str(seed["state"]), str(seed["state"]))
    return (
        f"自检{'通过' if report['ok'] else '未通过'}："
        f"运行环境={report['env']}，"
        f"业务模块={report['modules']}（路由 {report['registered_routers']}），"
        f"示例数据={state_text}（{seed['rows']}/{seed['seed_rows']} 条）"
    )


def bootstrap(settings: Settings, *, reset: bool = False) -> dict[str, Any]:
    """启动流程入口：（重新）装载示例数据并自检，返回自检报告。

    容器重启后进程内存清空，会重新灌入种子数据（reset=False）；重置入口在数据
    被改脏后调用（reset=True），二者走的是完全相同的装载与自检流程。
    """
    counts = store.reset_seed()
    logger.info("示例数据已%s：%d 个模块，共 %d 条记录",
                "重新装载" if reset else "装载", len(counts), sum(counts.values()))
    report = run_self_check(settings)
    logger.info(format_self_check(report))
    if not report["ok"]:
        logger.error("启动自检发现问题：缺模块=%s，多余模块=%s，种子状态=%s",
                     report["missing_modules"], report["extra_modules"], report["seed"]["state"])
    return report
