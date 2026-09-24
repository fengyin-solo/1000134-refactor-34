"""冷链物流温控运营平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health（返回运行环境、模块数量与示例数据状态）
重置示例数据：POST /api/seed/reset
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import bootstrap
from app.config import settings
from app.routers import ROUTERS
from app.store import store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """启动流程：读取运行环境、校验必要配置、确认示例数据就绪并打印自检结果。"""
    bootstrap.self_check()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in ROUTERS:
    app.include_router(module.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """健康检查：与启动日志同一份自检报告，含模块数量与示例数据状态。"""
    return bootstrap.build_report()


@app.post("/api/seed/reset")
def reset_seed() -> dict[str, object]:
    """重置示例数据：把被改脏的内存数据恢复成种子初始状态。"""
    if settings.env == "prod":
        raise HTTPException(status_code=403, detail="生产环境不允许重置示例数据")
    seed = bootstrap.reset_seed()
    return {"ok": True, "message": "示例数据已重置", "seed": seed}


@app.get("/api/overview")
def overview() -> dict[str, object]:
    """运营概览：把各业务模块的待处理量汇总成看板卡片。"""
    return store.overview()
