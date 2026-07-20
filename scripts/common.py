"""共享的项目路径、环境变量与 MySQL 连接配置。"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
STAR_DIR = PROJECT_ROOT / "data" / "star_csv"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_project_env() -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            "缺少 .env：请复制 .env.example 为 .env，并填写本机 MySQL 连接信息"
        )
    load_dotenv(ENV_FILE)
    required = ["MYSQL_USER", "MYSQL_PWD", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_DB"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f".env 缺少配置项：{', '.join(missing)}")


def mysql_url(*, include_database: bool = True) -> URL:
    load_project_env()
    return URL.create(
        "mysql+pymysql",
        username=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PWD"],
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        database=os.environ["MYSQL_DB"] if include_database else None,
        query={"charset": "utf8mb4"},
    )


def mysql_engine(*, include_database: bool = True) -> Engine:
    return create_engine(mysql_url(include_database=include_database), pool_pre_ping=True)


def ensure_output_dirs() -> None:
    STAR_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "notebooks").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "pdf").mkdir(parents=True, exist_ok=True)
