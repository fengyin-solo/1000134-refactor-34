"""运行配置：端口、跨域、运行环境。

取值来自 APP_ 前缀的环境变量，缺省时回落到本地开发默认值，
保证不配置任何东西也能直接起服务；格式非法的值在启动阶段就报错。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

KNOWN_ENVS = ("local", "dev", "test", "staging", "prod")

DEFAULT_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


@dataclass(frozen=True)
class Settings:
    app_name: str = "冷链物流温控运营平台"
    env: str = "local"
    port: int = 8000
    allowed_origins: list[str] = field(default_factory=lambda: list(DEFAULT_ORIGINS))
    page_size_default: int = 20
    page_size_max: int = 200

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量读取配置；格式非法时直接报错，不让服务带病启动。"""
        raw_port = os.getenv("APP_PORT", "8000").strip()
        try:
            port = int(raw_port)
        except ValueError:
            raise ValueError(f"APP_PORT 必须是整数，当前值：{raw_port!r}") from None
        raw_origins = os.getenv("APP_ALLOWED_ORIGINS", "").strip()
        origins = [item.strip() for item in raw_origins.split(",") if item.strip()]
        return cls(
            env=os.getenv("APP_ENV", "local").strip() or "local",
            port=port,
            allowed_origins=origins or list(DEFAULT_ORIGINS),
        )

    def validate(self) -> list[str]:
        """校验必要配置，返回问题列表；空列表表示全部通过。"""
        problems: list[str] = []
        if self.env not in KNOWN_ENVS:
            problems.append(f"APP_ENV 只能是 {'/'.join(KNOWN_ENVS)}，当前值：{self.env!r}")
        if not 1 <= self.port <= 65535:
            problems.append(f"APP_PORT 必须在 1-65535 之间，当前值：{self.port}")
        if not self.allowed_origins:
            problems.append("APP_ALLOWED_ORIGINS 至少要保留一个允许的来源")
        if self.page_size_default > self.page_size_max:
            problems.append("page_size_default 不能大于 page_size_max")
        return problems


settings = Settings.from_env()
