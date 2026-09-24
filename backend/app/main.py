"""冷链物流温控运营平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health（模块数量、示例数据状态，与启动日志同一口径）
重置示例数据：POST /api/seed/reset
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import bootstrap, logger, run_self_check
from app.config import settings
from app.routers import ROUTERS
from app.schemas import ActionResult
from app.store import store

logger.info("读取运行环境：APP_ENV=%s，端口=%d", settings.env, settings.port)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 统一启动流程：示例数据装载 + 启动自检，结果同时进日志与 app.state。
    app.state.self_check = bootstrap(settings)
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
def health() -> dict[str, Any]:
    """健康检查：服务存活、运行环境、模块注册数量与示例数据状态。

    自检口径与启动流程（app.bootstrap.run_self_check）完全一致，
    示例数据被改脏后这里会实时反映出来，可用 POST /api/seed/reset 恢复。
    """
    report = run_self_check(settings)
    return {
        "ok": report["ok"],
        "app": settings.app_name,
        "env": report["env"],
        "modules": report["modules"],
        "seed": report["seed"],
    }


@app.post("/api/seed/reset", response_model=ActionResult)
def reset_seed() -> ActionResult:
    """把被改脏的示例数据丢弃并重新装载，随后按启动流程再做一次自检。"""
    report = bootstrap(settings, reset=True)
    state = report["seed"]["state"]
    if not report["ok"] or state != "pristine":
        return ActionResult(ok=False, message=f"示例数据重置后自检未通过（状态：{state}）")
    return ActionResult(
        ok=True,
        message=f"示例数据已重置为初始状态（{report['modules']} 个模块，"
                f"{report['seed']['rows']} 条记录）",
    )


@app.get("/api/overview")
def overview() -> dict[str, object]:
    """运营概览：把各业务模块的待处理量汇总成看板卡片。"""
    return store.overview()
