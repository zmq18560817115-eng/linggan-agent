"""Pydantic 数据结构，对应技术方案「六、AI输出结构」。"""
from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel


# ---------- AI 输出结构 ----------
class ColorSystem(BaseModel):
    palette: list[str] = []          # 主要色值
    primary: str = ""                # 主色
    description: str = ""            # 色彩体系描述


class Composition(BaseModel):
    type: str = ""                   # 构图方式（居中/对称/三分/留白...）
    description: str = ""


class Light(BaseModel):
    type: str = ""                   # 光影语言
    description: str = ""


class Layout(BaseModel):
    """排版拆解。"""

    layout_type: str = ""            # 版式类型（满版/中轴/分栏/网格/留白...）
    alignment: str = ""              # 对齐方式
    hierarchy: list[str] = []        # 信息层级（主标题>副标题>正文...）
    whitespace: str = ""             # 留白策略
    focal: str = ""                  # 视觉重心 / 阅读引导路径
    description: str = ""


class Typography(BaseModel):
    """文字 / 标题 / 字体拆解。"""

    title_treatment: str = ""        # 标题处理方式
    font_tone: str = ""              # 字体调性建议（无衬线/衬线/手写...）
    size_contrast: str = ""          # 字号层级对比
    pairing: str = ""                # 中英文 / 主辅字体搭配
    text_ratio: str = ""             # 文字占比（重文字/图文均衡/以图为主）
    description: str = ""


class VisualStyle(BaseModel):
    style_tags: list[str] = []       # 风格标签
    mood_keywords: list[str] = []    # 情绪关键词
    brand_position: str = ""         # 品牌定位


class DesignRules(BaseModel):
    why_good: list[str] = []         # 为什么优秀
    reusable_methods: list[str] = []  # 可复用方法


class CaseBasics(BaseModel):
    image_type: str = ""             # 图片类型
    industry: str = ""               # 行业
    scene: str = ""                  # 使用场景


class AnalysisResult(BaseModel):
    """一次完整的 AI 拆解输出。"""

    basics: CaseBasics
    style: VisualStyle
    color: ColorSystem
    composition: Composition
    light: Light
    material: str = ""               # 材质表现
    layout: Layout                   # 排版
    typography: Typography           # 文字 / 标题 / 字体
    design_rules: DesignRules
    prompt: str = ""                 # AI 绘图提示词
    summary: str = ""                # 一句话总结
    name: str = ""                   # 案例名称
    tags: list[str] = []             # 汇总标签


# ---------- API 出参 ----------
class ImageOut(BaseModel):
    id: int
    url: str
    filename: str
    source: str
    uploader: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class TagOut(BaseModel):
    id: int
    name: str
    category: str

    class Config:
        from_attributes = True


class CaseOut(BaseModel):
    id: int
    name: str
    industry: str
    scene: str
    summary: str
    created_at: dt.datetime
    image: ImageOut | None = None
    tags: list[TagOut] = []
    analysis: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class RequirementInput(BaseModel):
    """需求生成页入参。"""

    text: str
    industry: str = ""


class VisualDirection(BaseModel):
    """需求 → 视觉方向 推荐结果。"""

    directions: list[str]
    recommended_tags: list[str]
    reference_case_ids: list[int]
    prompt: str
