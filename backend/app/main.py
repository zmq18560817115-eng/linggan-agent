"""FastAPI 应用入口（对应技术方案「三、系统整体架构」的后端 API 层）。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import config, crud, models
from .agents import run_pipeline
from .database import get_db, init_db
from .schemas import CaseOut, RequirementInput, VisualDirection

app = FastAPI(
    title="AI视觉拆解 Agent",
    description="优秀案例图片 → AI视觉理解 → 设计拆解 → 案例资产卡 → 团队复用",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态托管上传的图片
app.mount("/uploads", StaticFiles(directory=str(config.UPLOAD_DIR)), name="uploads")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "vision_provider": config.VISION_PROVIDER}


@app.post("/api/analyze", response_model=CaseOut)
async def analyze_image(
    file: UploadFile = File(...),
    uploader: str = "anonymous",
    db: Session = Depends(get_db),
):
    """上传图片 → 运行 AI Agent 流水线 → 生成并保存案例卡。

    覆盖技术方案 MVP 核心功能：图片上传 / AI视觉分析 / 自动生成案例卡。
    """
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    ext = Path(file.filename or "").suffix or ".png"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = config.UPLOAD_DIR / stored_name
    dest.write_bytes(await file.read())

    image = models.Image(
        url=f"/uploads/{stored_name}",
        filename=file.filename or stored_name,
        source="upload",
        uploader=uploader,
    )
    db.add(image)
    db.flush()

    try:
        result = run_pipeline(str(dest))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"分析失败：{exc}") from exc

    case = crud.create_case_from_analysis(db, image, result)
    return crud.serialize_case(case)


@app.get("/api/cases", response_model=list[CaseOut])
def list_cases(q: str | None = None, tag: str | None = None, db: Session = Depends(get_db)):
    """案例资产库：支持关键词搜索与标签检索。"""
    cases = crud.search_cases(db, q=q, tag=tag)
    return [crud.serialize_case(c) for c in cases]


@app.get("/api/cases/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return crud.serialize_case(case)


@app.get("/api/tags")
def list_tags(db: Session = Depends(get_db)):
    """返回标签及其案例数量，用于首页热门风格 / 检索。"""
    tags = db.query(models.Tag).all()
    return [
        {"id": t.id, "name": t.name, "category": t.category, "count": len(t.cases)}
        for t in tags
    ]


@app.post("/api/recommend", response_model=VisualDirection)
def recommend_direction(payload: RequirementInput, db: Session = Depends(get_db)):
    """需求生成页：需求文本 → 推荐视觉方向（对应「未来升级 V3.0」雏形）。"""
    text = payload.text.lower()
    keyword_map = {
        "科技": ["科技感", "冷调", "极简"],
        "高端": ["高级感", "克制", "低饱和"],
        "年轻": ["年轻化", "活力", "高饱和"],
        "温暖": ["温暖感", "亲和", "暖调"],
        "简约": ["极简", "干净", "留白"],
    }
    hit_tags: list[str] = []
    for kw, tags in keyword_map.items():
        if kw in text or kw in payload.industry:
            hit_tags.extend(tags)
    if not hit_tags:
        hit_tags = ["高级感", "极简", "克制"]
    hit_tags = list(dict.fromkeys(hit_tags))

    # 从案例库中检索匹配标签的参考案例
    refs: list[int] = []
    for c in crud.search_cases(db):
        if any(t.name in hit_tags for t in c.tags):
            refs.append(c.id)
        if len(refs) >= 4:
            break

    directions = [
        f"主打「{hit_tags[0]}」风格，" + ("冷色科技调" if "科技感" in hit_tags else "统一低饱和色板"),
        f"构图建议：居中聚焦 + 留白，突出核心信息",
        f"情绪关键词：{'、'.join(hit_tags[1:3]) or '克制、干净'}",
    ]
    prompt = (
        f"{payload.industry or '品牌'}视觉，{'、'.join(hit_tags)}风格，"
        "高质量, 商业级, 精致细节, 8k"
    )
    return VisualDirection(
        directions=directions,
        recommended_tags=hit_tags,
        reference_case_ids=refs,
        prompt=prompt,
    )
