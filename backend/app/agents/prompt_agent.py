"""Prompt Agent —— 生成 AI 绘图提示词。

对应技术方案「五、AI Agent流程 5. Prompt Agent」。
将拆解结果反向组合成可直接用于 AI 绘图的提示词。
"""
from __future__ import annotations

from ..schemas import CaseBasics, ColorSystem, Light, VisualStyle
from ..vision_provider import ImageFeatures


def run(
    features: ImageFeatures,
    basics: CaseBasics,
    style: VisualStyle,
    color: ColorSystem,
    light: Light,
    material: str,
) -> str:
    tone = "warm tones" if features.warm else "cool tones"
    parts = [
        f"{basics.image_type}, {basics.industry} 行业视觉",
        "、".join(style.style_tags),
        f"色彩：{'、'.join(features.color_names[:3]) or '中性色'}（{tone}），主色 {color.primary}",
        f"光影：{light.type}",
        f"材质：{material}",
        f"情绪：{'、'.join(style.mood_keywords)}",
        "高质量, 商业级, 精致细节, 8k",
    ]
    zh = "，".join(p for p in parts if p)
    en = (
        f"{basics.industry} visual, {', '.join(style.style_tags)} style, "
        f"{tone}, primary color {color.primary}, {light.type} lighting, "
        f"{material}, {', '.join(style.mood_keywords)} mood, "
        "high quality, commercial grade, intricate details, 8k"
    )
    return f"{zh}\n\nEN: {en}"
