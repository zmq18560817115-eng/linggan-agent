"""数据持久化与查询逻辑。"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from . import models
from .schemas import AnalysisResult


def get_or_create_tag(db: Session, name: str, category: str = "style") -> models.Tag:
    name = name.strip()
    tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if not tag:
        tag = models.Tag(name=name, category=category)
        db.add(tag)
        db.flush()
    return tag


def create_case_from_analysis(
    db: Session, image: models.Image, result: AnalysisResult
) -> models.Case:
    """将一次 AI 拆解结果落库为完整案例卡。"""
    case = models.Case(
        image_id=image.id,
        name=result.name,
        industry=result.basics.industry,
        scene=result.basics.scene,
        summary=result.summary,
    )
    db.add(case)
    db.flush()

    analysis = models.Analysis(
        case_id=case.id,
        color=result.color.model_dump_json(),
        composition=result.composition.model_dump_json(),
        light=result.light.model_dump_json(),
        style=result.style.model_dump_json(),
        design_rules=result.design_rules.model_dump_json(),
        prompt=result.prompt,
    )
    db.add(analysis)

    for name in result.tags:
        if not name:
            continue
        case.tags.append(get_or_create_tag(db, name))

    db.commit()
    db.refresh(case)
    return case


def analysis_to_dict(analysis: models.Analysis | None) -> dict | None:
    if not analysis:
        return None
    return {
        "color": json.loads(analysis.color or "{}"),
        "composition": json.loads(analysis.composition or "{}"),
        "light": json.loads(analysis.light or "{}"),
        "style": json.loads(analysis.style or "{}"),
        "design_rules": json.loads(analysis.design_rules or "{}"),
        "material": getattr(analysis, "material", ""),
        "prompt": analysis.prompt or "",
    }


def serialize_case(case: models.Case) -> dict:
    return {
        "id": case.id,
        "name": case.name,
        "industry": case.industry,
        "scene": case.scene,
        "summary": case.summary,
        "created_at": case.created_at,
        "image": case.image,
        "tags": case.tags,
        "analysis": analysis_to_dict(case.analysis),
    }


def search_cases(
    db: Session, q: str | None = None, tag: str | None = None
) -> list[models.Case]:
    query = db.query(models.Case)
    if tag:
        query = query.join(models.Case.tags).filter(models.Tag.name == tag)
    cases = query.order_by(models.Case.created_at.desc()).all()
    if q:
        ql = q.lower()
        cases = [
            c
            for c in cases
            if ql in (c.name or "").lower()
            or ql in (c.summary or "").lower()
            or ql in (c.industry or "").lower()
            or any(ql in t.name.lower() for t in c.tags)
        ]
    return cases
