"""AI Agent 流水线编排。

串联 Vision → Style → Design → Layout → Rule → Prompt 六个 Agent，
输出技术方案「六、AI输出结构」定义的完整拆解结果
（含色彩、构图、光影、材质、排版、文字/标题/字体）。
"""
from __future__ import annotations

from ..schemas import AnalysisResult
from ..vision_provider import analyze
from . import (
    design_agent,
    layout_agent,
    prompt_agent,
    rule_agent,
    style_agent,
    vision_agent,
)


def run_pipeline(image_path: str) -> AnalysisResult:
    features = analyze(image_path)

    basics = vision_agent.run(features)
    style = style_agent.run(features)
    color, composition, light, material = design_agent.run(features)
    layout, typography = layout_agent.run(features)
    rules = rule_agent.run(
        features, basics, style, color, composition, light, layout, typography
    )
    prompt = prompt_agent.run(
        features, basics, style, color, light, material, layout, typography
    )

    # 案例名称与总结
    name = f"{basics.industry}·{'/'.join(style.style_tags[:2])}视觉案例"
    summary = (
        f"一张{basics.image_type}，呈现{'、'.join(style.style_tags)}风格，"
        f"{color.description}排版为{layout.layout_type}，{typography.text_ratio}。"
    )

    # 汇总标签（供检索）——加入排版与文字维度
    tags = list(
        dict.fromkeys(
            style.style_tags
            + style.mood_keywords
            + [
                basics.industry,
                basics.scene,
                composition.type,
                light.type,
                layout.layout_type,
                layout.alignment,
                typography.text_ratio,
                typography.font_tone.split("（")[0].split("/")[0].strip(),
            ]
        )
    )

    return AnalysisResult(
        basics=basics,
        style=style,
        color=color,
        composition=composition,
        light=light,
        material=material,
        layout=layout,
        typography=typography,
        design_rules=rules,
        prompt=prompt,
        summary=summary,
        name=name,
        tags=tags,
    )
