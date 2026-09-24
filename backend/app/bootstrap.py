"""共用启动流程：读取运行环境、校验必要配置、确认示例数据就绪。

健康检查、示例数据初始化、运行环境读取原来散在各处各写各的，这里收拢成一份：
- self_check() 在启动时执行，打印的日志与健康检查接口返回的是同一份报告，
  容器重启后两边结果必然一致；
- reset_seed() 是示例数据的重置入口，重置后同样输出一行日志。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings
from app.store import store

logger = logging.getLogger("app.bootstrap")


def build_report() -> dict[str, Any]:
    """汇总当前运行状态：运行环境、必要配置、模块数量与示例数据状态。"""
    return {
        "ok": True,
        "app": settings.app_name,
        "env": settings.env,
        "port": settings.port,
        "allowed_origins": settings.allowed_origins,
        "modules": len(store.module_names()),
        "seed": store.seed_status(),
    }


def self_check() -> dict[str, Any]:
    """启动自检：校验必要配置，确认示例数据就绪，并打印与接口一致的报告。"""
    problems = settings.validate()
    if problems:
        raise RuntimeError("配置校验未通过：" + "；".join(problems))
    report = build_report()
    logger.info("启动自检通过：%s", json.dumps(report, ensure_ascii=False))
    return report


def reset_seed() -> dict[str, Any]:
    """重置示例数据并返回最新状态。"""
    store.reset()
    seed = store.seed_status()
    logger.info("示例数据已重置：%s", json.dumps(seed, ensure_ascii=False))
    return seed
