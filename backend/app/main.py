"""FastAPI 应用入口（对应技术方案「三、系统整体架构」的后端 API 层）。"""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import concept, config, crud, llm, models, overlay
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
    vlm_on = config.vlm_enabled()
    return {
        "status": "ok",
        "vision_provider": config.VISION_PROVIDER,
        "vlm_enabled": vlm_on,
        "model": config.VISION_MODEL if vlm_on else "启发式规则",
        "llm_enabled": config.llm_enabled(),
        "llm_model": config.LLM_MODEL if config.llm_enabled() else "",
    }


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


@app.get("/api/cases/{case_id}/overlay")
def case_layout_overlay(case_id: int, db: Session = Depends(get_db)):
    """返回叠加了版式骨架（页边距/模块/栅格）的案例图 PNG。"""
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case or not case.image:
        raise HTTPException(status_code=404, detail="案例或图片不存在")
    path = config.UPLOAD_DIR / Path(case.image.url).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    try:
        png = overlay.render_overlay(str(path))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"骨架渲染失败：{exc}") from exc
    return Response(content=png, media_type="image/png")


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


@app.get("/api/concept")
def get_concept(db: Session = Depends(get_db)):
    """设计视觉概论：跨案例聚合出的分布画像、视觉 DNA 与提炼的设计原则。"""
    return concept.build_concept(db)


@app.post("/api/concept/methodology")
def concept_methodology(db: Session = Depends(get_db)):
    """用文本大模型把聚合数据写成成体系的设计方法论（需配置 LLM_*）。"""
    data = concept.build_concept(db)
    try:
        return concept.synthesize_methodology(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"方法论生成失败：{exc}") from exc


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
            # 意向图：以「排版」为主要参考、风格为次要参考。
            # 排版维度置于标签最前（权重最高），风格与情绪其次。
            layout_tags = [
                ref.layout.layout_type,
                ref.layout.alignment,
                ref.typography.text_ratio,
            ]
            hit_tags = layout_tags + ref.style.style_tags + ref.style.mood_keywords[:2] + hit_tags

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
        # 排版为主要参考 —— 放在第一条，作为生图的核心骨架
        directions.append(
            f"【主要·排版】沿用意向图版式：{ref.layout.layout_type}，{ref.layout.alignment}；"
            f"信息层级：{' → '.join(ref.layout.hierarchy)}"
        )
        directions.append(
            f"【主要·栅格】{ref.layout.grid_columns}；{ref.layout.modules}；"
            f"{ref.layout.margins}；{ref.layout.spacing}"
        )
        directions.append(
            f"【主要·文字】{ref.typography.title_treatment}；字体调性「{ref.typography.font_tone}」；"
            f"{ref.typography.text_ratio}，{ref.typography.size_contrast}"
        )
        # 风格为次要参考
        directions.append(
            f"【次要·风格】风格倾向 {'、'.join(ref.style.style_tags)}，"
            f"色板参考主色 {ref.color.primary}（{'、'.join(ref.color.palette[:3])}），可结合需求微调"
        )
        directions.append(f"情绪关键词：{'、'.join(ref.style.mood_keywords)}")
        palette_hint = "、".join(ref.color.palette[:4])
        # 提示词：排版/信息层级在前（主），风格/色彩在后（次）
        prompt = (
            f"{industry or '品牌'}视觉；"
            f"【版式为主】{ref.layout.layout_type}，{ref.layout.grid_columns}，"
            f"{ref.layout.modules}，{ref.layout.alignment}，{ref.layout.margins}，"
            f"信息层级 {' → '.join(ref.layout.hierarchy)}，{ref.typography.title_treatment}，"
            f"字体{ref.typography.font_tone}；"
            f"【风格为辅】{'、'.join(ref.style.style_tags)}，参考色板 {palette_hint}"
            f"（主色 {ref.color.primary}），{ref.light.type}光影；"
            + (f"需求：{text}；" if text else "")
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

    # 需求解读增强：配置了文本模型时，用其把需求+意向图解析成更贴合的方向与提示词
    if config.llm_enabled() and (text.strip() or ref is not None):
        try:
            ref_ctx = ""
            if ref is not None:
                ref_ctx = (
                    f"意向图解析：版式 {ref.layout.layout_type}/{ref.layout.grid_columns}，"
                    f"风格 {'、'.join(ref.style.style_tags)}，主色 {ref.color.primary}。"
                )
            j = llm.chat_json(
                [
                    {"role": "system", "content": "你是资深视觉设计顾问，只输出 JSON，不要多余文字。"},
                    {
                        "role": "user",
                        "content": (
                            f"需求：{text or '（仅意向图，无文字需求）'}；行业：{industry or '未指定'}；"
                            f"{ref_ctx}参考标签：{'、'.join(hit_tags)}。\n"
                            '请输出 JSON：{"directions":["3~4 条以版式为主、风格为辅的视觉方向"],'
                            '"prompt":"一条可直接用于 AI 绘图的中文提示词，版式为主风格为辅"}'
                        ),
                    },
                ],
                temperature=0.5,
            )
            if isinstance(j.get("directions"), list) and j["directions"]:
                directions = [str(x) for x in j["directions"]]
            if j.get("prompt"):
                prompt = str(j["prompt"])
        except Exception:
            pass  # 模型不可用时保留启发式结果

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
