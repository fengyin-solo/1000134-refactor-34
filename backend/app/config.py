"""运行配置：运行环境、端口、跨域。

配置在进程启动时从环境变量读取一次（见 load_settings），读取的同时完成校验：
运行环境必须是已知取值，端口要在合法范围，跨域来源必须是 http(s) 地址。
任何一项不合法都直接抛出 ConfigError，让服务在启动阶段就失败，而不是带着
错误配置跑起来之后再出现奇怪的行为。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

VALID_ENVS = ("local", "dev", "staging", "prod")


class ConfigError(ValueError):
    """必要配置缺失或不合法：启动阶段直接失败并给出可读原因。"""


@dataclass(frozen=True)
class Settings:
    app_name: str
    env: str
    port: int
    allowed_origins: list[str] = field(default_factory=list)
    page_size_default: int = 20
    page_size_max: int = 200


def _parse_origins(raw: str | None) -> list[str]:
    if not raw or not raw.strip():
        origins = ["http://127.0.0.1:5173", "http://localhost:5173"]
    else:
        origins = [item.strip() for item in raw.split(",") if item.strip()]
    for origin in origins:
        if not origin.startswith(("http://", "https://")):
            raise ConfigError(
                f"APP_ALLOWED_ORIGINS 里的跨域来源「{origin}」必须以 http:// 或 https:// 开头"
            )
    if not origins:
        raise ConfigError("APP_ALLOWED_ORIGINS 至少要保留一个跨域来源")
    return origins


def load_settings() -> Settings:
    """从环境变量读取配置并校验；默认值对应本地开发，流程与改造前一致。"""
    env = os.environ.get("APP_ENV", "local").strip() or "local"
    if env not in VALID_ENVS:
        raise ConfigError(
            f"APP_ENV={env!r} 不是支持的运行环境，可选：{ '、'.join(VALID_ENVS) }"
        )

    app_name = os.environ.get("APP_NAME", "冷链物流温控运营平台").strip()
    if not app_name:
        raise ConfigError("APP_NAME 不能为空")

    raw_port = os.environ.get("APP_PORT", "8000").strip()
    try:
        port = int(raw_port)
    except ValueError:
        raise ConfigError(f"APP_PORT={raw_port!r} 不是合法端口号") from None
    if not 1 <= port <= 65535:
        raise ConfigError(f"APP_PORT={port} 超出 1-65535 的合法范围")

    allowed_origins = _parse_origins(os.environ.get("APP_ALLOWED_ORIGINS"))

    return Settings(
        app_name=app_name,
        env=env,
        port=port,
        allowed_origins=allowed_origins,
    )


settings = load_settings()
