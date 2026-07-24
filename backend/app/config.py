"""应用配置。

通过环境变量控制视觉模型服务的接入方式。未配置任何真实模型时，
系统会自动退回到基于 Pillow 的启发式视觉分析器，保证 Demo 可以离线运行。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 上传图片存储目录
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 数据库（Demo 默认使用 SQLite；生产可切换 PostgreSQL / Supabase）
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'linggan.db'}")

# 视觉模型服务配置（可选）
#   VISION_PROVIDER: mock | openai | qwen
#   VISION_API_KEY / VISION_BASE_URL / VISION_MODEL: 对应服务的凭证
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "mock").lower()
VISION_API_KEY = os.getenv("VISION_API_KEY", "")
VISION_BASE_URL = os.getenv("VISION_BASE_URL", "")
VISION_MODEL = os.getenv("VISION_MODEL", "")

# 允许的前端跨域来源
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
