"""数据库连接与会话管理。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401  确保模型被注册

    Base.metadata.create_all(bind=engine)
    _auto_migrate()


def _auto_migrate():
    """轻量迁移：为已存在的旧表补齐新增列（避免升级后需手动删库）。"""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "analysis" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("analysis")}
    # 列名 -> 默认值
    new_cols = {"material": "", "layout": "{}", "typography": "{}"}
    for col, default in new_cols.items():
        if col not in existing:
            with engine.begin() as conn:
                conn.execute(
                    text(f"ALTER TABLE analysis ADD COLUMN {col} TEXT DEFAULT '{default}'")
                )
