"""FastAPI 应用入口（对应技术方案「三、系统整体架构」的后端 API 层）。"""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import config, crud, models
from .agents import run_pipeline
from .database import get_db, init_db
from .schemas import AnalysisResult, CaseOut, VisualDirection

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


def _analyze_reference(file: UploadFile, data: bytes) -> AnalysisResult:
    """对上传的意向图做视觉拆解（不落库，仅用于推荐）。"""
    ext = Path(file.filename or "").suffix or ".png"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        tmp.write(data)
        tmp.close()
        return run_pipeline(tmp.name)
    finally:
        os.unlink(tmp.name)


@app.post("/api/recommend", response_model=VisualDirection)
async def recommend_direction(
    text: str = Form(""),
    industry: str = Form(""),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """需求生成页：需求文本（+ 可选意向图）→ 推荐视觉方向与绘图提示词。

    对应技术方案「未来升级 V3.0」：需求输入 → 视觉方向 → 意向图生成。
    上传意向图时，会先对其做视觉拆解，并把风格/色彩/排版融合进推荐。
    """
    low = text.lower()
    keyword_map = {
        "科技": ["科技感", "冷调", "极简"],
        "高端": ["高级感", "克制", "低饱和"],
        "年轻": ["年轻化", "活力", "高饱和"],
        "温暖": ["温暖感", "亲和", "暖调"],
        "简约": ["极简", "干净", "留白"],
    }
    hit_tags: list[str] = []
    for kw, tags in keyword_map.items():
        if kw in low or kw in industry:
            hit_tags.extend(tags)

    # —— 解析意向图（若有）——
    ref: AnalysisResult | None = None
    if file is not None and (file.filename or ""):
        data = await file.read()
        if data:
            if not (file.content_type or "").startswith("image/"):
                raise HTTPException(status_code=400, detail="意向图必须是图片文件")
            try:
                ref = _analyze_reference(file, data)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=500, detail=f"意向图解析失败：{exc}") from exc
            # 参考图的风格与情绪并入推荐标签（权重更高，放前面）
            hit_tags = ref.style.style_tags + ref.style.mood_keywords[:2] + hit_tags

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

    # —— 组织方向与提示词 ——
    directions: list[str] = []
    if ref is not None:
        directions.append(
            f"延续意向图调性：{'、'.join(ref.style.style_tags)}；"
            f"沿用其{ref.layout.layout_type}排版与{ref.color.description}"
        )
        directions.append(
            f"色板参考意向图主色 {ref.color.primary}（{'、'.join(ref.color.palette[:3])}），"
            "结合需求做微调"
        )
        directions.append(
            f"标题/字体建议：{ref.typography.title_treatment}，字体调性「{ref.typography.font_tone}」"
        )
        directions.append(f"情绪关键词：{'、'.join(hit_tags[:4])}")
        palette_hint = "、".join(ref.color.palette[:4])
        prompt = (
            f"{industry or '品牌'}视觉，{'、'.join(hit_tags)}风格，"
            f"参考色板 {palette_hint}（主色 {ref.color.primary}），"
            f"{ref.layout.layout_type}排版，{ref.light.type}光影，"
            f"字体{ref.typography.font_tone}，"
            + (f"需求：{text}，" if text else "")
            + "高质量, 商业级, 精致细节, 8k"
        )
    else:
        directions = [
            f"主打「{hit_tags[0]}」风格，"
            + ("冷色科技调" if "科技感" in hit_tags else "统一低饱和色板"),
            "构图建议：居中聚焦 + 留白，突出核心信息",
            f"情绪关键词：{'、'.join(hit_tags[1:3]) or '克制、干净'}",
        ]
        prompt = (
            f"{industry or '品牌'}视觉，{'、'.join(hit_tags)}风格，"
            + (f"需求：{text}，" if text else "")
            + "高质量, 商业级, 精致细节, 8k"
        )

    return VisualDirection(
        directions=directions,
        recommended_tags=hit_tags,
        reference_case_ids=refs,
        prompt=prompt,
        has_reference=ref is not None,
        reference_style=ref.style.style_tags if ref else [],
        reference_palette=ref.color.palette if ref else [],
        reference_layout=ref.layout.layout_type if ref else "",
        reference_font=ref.typography.font_tone if ref else "",
        reference_summary=ref.summary if ref else "",
    )
