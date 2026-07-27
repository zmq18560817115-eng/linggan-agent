# linggan-agent · AI视觉拆解 Agent

> 优秀的图文拆解素材库 —— 把优秀案例图片，沉淀为团队可复用的视觉知识资产。
>
> **优秀案例图片 → AI视觉理解 → 设计拆解 → 案例资产卡 → 团队复用**

本仓库是《AI视觉拆解 Agent Demo 技术实现方案 V1.0》的 MVP 实现。

## 解决的问题

1. 需求方无法准确描述视觉方向 → 提供「需求 → 视觉方向」推荐。
2. 设计经验依赖个人，无法沉淀 → 自动生成结构化案例资产卡并入库。
3. 优秀案例无法转化为设计规则 → Rule Agent 总结「为什么优秀 / 可复用方法」。

## 系统架构

```
用户 → Web前端(Next.js) → 后端API(FastAPI) → AI视觉分析服务
                                              → 数据库与素材存储 → 视觉知识库
```

## AI Agent 流水线

上传图片后，后端依次运行 5 个 Agent（`backend/app/agents/`）：

| Agent | 职责 |
|-------|------|
| Vision Agent | 识别图片类型、行业、使用场景 |
| Style Agent | 分析视觉风格（高级感/科技感/温暖感/年轻化…）与情绪 |
| Design Agent | 拆解色彩、构图、光影、材质 |
| Layout Agent | 拆解排版与文字架构：版式类型、信息层级、对齐、留白、标题处理、字体调性、文字占比 |
| Rule Agent | 总结设计规律：为什么优秀 / 可复用方法 |
| Prompt Agent | 反向生成 AI 绘图提示词（中/英） |

> 视觉拆解覆盖两大维度：**画面层**（色彩·构图·光影·材质）与 **信息层**（排版·信息层级·标题·字体），
> 不止「风格像不像」，还回答「版面怎么排、字怎么放」。

**拆解采用混合模式**（详见 [docs/拆解规则说明.md](./docs/拆解规则说明.md)）：
- **客观特征层**（Pillow）：真实主色板、亮度、对比度、冷暖，以及页边距/栅格列数/模块数等**硬版式参数**——精确、可复现，无需任何 API Key 即可离线跑通。
- **语义层**：默认用启发式规则；配置环境变量后切换到**真实视觉大模型**（GPT Vision / Qwen-VL / 内网自建），由模型负责语义理解，硬参数仍用像素测量值，调用失败自动回退。

## 技术选型

- 前端：Next.js 14（App Router）+ Tailwind CSS
- 后端：FastAPI + Python 3.11
- 数据库：SQLAlchemy + SQLite（Demo；生产可切 PostgreSQL / Supabase）
- 视觉分析：Pillow 启发式 / 可插拔 VLM

## 目录结构

```
backend/
  app/
    main.py            # FastAPI 入口与 API 路由
    config.py          # 环境变量配置
    database.py        # DB 连接
    models.py          # images / cases / analysis / tags 四表
    schemas.py         # AI 输出结构（对应方案「六」）
    crud.py            # 落库与检索
    vision_provider.py # 视觉特征提取（可插拔真实大模型）
    agents/            # 5 个 Agent + pipeline 编排
frontend/
  app/                 # 首页 / 案例库 / AI拆解 / 案例详情 / 需求生成
  components/ui.tsx    # 通用组件
  lib/api.ts           # 后端 API 封装
```

## 部署

内网/生产部署（Docker Compose 一键、离线镜像导入、Nginx 反代等）见 **[DEPLOY.md](./DEPLOY.md)**。
最简形式：

```bash
git clone https://github.com/zmq18560817115-eng/linggan-agent.git
cd linggan-agent
docker compose up -d --build   # 前端 :3000  后端 :8000
```

## 快速启动

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

### 2. 前端

```bash
cd frontend
npm install
npm run dev        # 开发模式，http://localhost:3000
# 或 npm run build && npm run start
```

前端通过 `next.config.js` 的 rewrites 将 `/api`、`/uploads` 代理到后端，
默认后端地址 `http://127.0.0.1:8000`，可用 `BACKEND_URL` 覆盖。

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 上传图片 → 运行流水线 → 生成并保存案例卡 |
| GET  | `/api/cases?q=&tag=` | 案例库检索（关键词 + 标签） |
| GET  | `/api/cases/{id}` | 案例详情 |
| GET  | `/api/tags` | 标签及案例数（热门风格） |
| GET  | `/api/concept` | 设计视觉概论：跨案例聚合的分布/DNA/设计原则 |
| POST | `/api/recommend` | 需求文本 → 推荐视觉方向 |

## 接入真实视觉大模型

OpenAI 兼容接口，兼容 GPT Vision、Qwen-VL（DashScope 兼容模式）、内网自建服务（vLLM/LMDeploy 等）：

```bash
# GPT Vision
export VISION_PROVIDER=openai
export VISION_API_KEY=sk-xxx
export VISION_BASE_URL=https://api.openai.com/v1
export VISION_MODEL=gpt-4o-mini

# 或 Qwen-VL（阿里云 DashScope 兼容模式）
export VISION_PROVIDER=qwen
export VISION_API_KEY=sk-xxx
export VISION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export VISION_MODEL=qwen-vl-max

# 或 火山引擎 · 豆包视觉（Ark 方舟，OpenAI 兼容）
export VISION_PROVIDER=volcengine
export VISION_API_KEY=<火山方舟 API Key>
export VISION_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
export VISION_MODEL=<接入点ID ep-xxxx 或 doubao-vision 模型名>
```

- 未配置时自动使用离线启发式分析器，Demo 开箱即用。
- 配置后仅语义层用大模型；真实色板与硬版式参数仍由 Pillow 精确测量；调用失败自动回退。
- 拆解规则与实现细节见 [docs/拆解规则说明.md](./docs/拆解规则说明.md)。

## 路线图

- **V1.0（当前）**：图片上传、AI 拆解、案例卡入库、标签检索、需求推荐。
- **V2.0**：接入 CLIP 视觉向量搜索（ChromaDB / Milvus / Supabase Vector），实现图片语义检索与相似案例。
- **V3.0**：完整需求理解系统：需求输入 → 视觉方向 → 意向图生成。

最终目标：将设计师个人经验，转化为企业共享的 AI 视觉知识资产。
