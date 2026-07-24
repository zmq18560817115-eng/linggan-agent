"""数据库模型。

对应技术方案「七、数据库设计」中的四张核心表：
images（图片表）、cases（案例表）、analysis（分析结果表）、tags（标签表）。
"""
import datetime as dt

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base

# 案例与标签的多对多关联表
case_tags = Table(
    "case_tags",
    Base.metadata,
    Column("case_id", ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Image(Base):
    """图片表：记录上传的原始素材。"""

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)          # 可访问的图片地址
    filename = Column(String, nullable=False)
    source = Column(String, default="upload")     # 来源
    uploader = Column(String, default="anonymous")  # 上传人
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    case = relationship("Case", back_populates="image", uselist=False)


class Case(Base):
    """案例表：一张图片拆解后形成的「案例资产卡」。"""

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    industry = Column(String, default="")        # 行业
    scene = Column(String, default="")           # 使用场景
    summary = Column(Text, default="")           # 一句话总结
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    image = relationship("Image", back_populates="case")
    analysis = relationship(
        "Analysis", back_populates="case", uselist=False, cascade="all, delete-orphan"
    )
    tags = relationship("Tag", secondary=case_tags, back_populates="cases")


class Analysis(Base):
    """分析结果表：AI Agent 流水线输出的结构化拆解结果。"""

    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    # 以 JSON 文本存储，兼顾 SQLite 与 PostgreSQL
    color = Column(Text, default="{}")       # 色彩体系
    composition = Column(Text, default="{}") # 构图方式
    light = Column(Text, default="{}")       # 光影语言
    style = Column(Text, default="{}")       # 视觉风格 JSON
    design_rules = Column(Text, default="{}")  # 设计规则
    prompt = Column(Text, default="")        # AI 绘图提示词

    case = relationship("Case", back_populates="analysis")


class Tag(Base):
    """标签表：支持分类与层级关系。"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, default="style")  # 分类：style/industry/scene/mood...
    parent_id = Column(Integer, ForeignKey("tags.id"), nullable=True)  # 层级关系

    cases = relationship("Case", secondary=case_tags, back_populates="tags")
