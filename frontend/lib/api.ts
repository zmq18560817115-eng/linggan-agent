// 后端 API 封装。开发时通过 next.config.js 的 rewrites 代理到 FastAPI。

export interface TagOut {
  id: number;
  name: string;
  category: string;
}

export interface ImageOut {
  id: number;
  url: string;
  filename: string;
}

export interface AnalysisData {
  color: { palette: string[]; primary: string; description: string };
  composition: { type: string; description: string };
  light: { type: string; description: string };
  layout: {
    layout_type: string;
    alignment: string;
    hierarchy: string[];
    whitespace: string;
    focal: string;
    description: string;
  };
  typography: {
    title_treatment: string;
    font_tone: string;
    size_contrast: string;
    pairing: string;
    text_ratio: string;
    description: string;
  };
  style: { style_tags: string[]; mood_keywords: string[]; brand_position: string };
  design_rules: { why_good: string[]; reusable_methods: string[] };
  material: string;
  prompt: string;
}

export interface CaseOut {
  id: number;
  name: string;
  industry: string;
  scene: string;
  summary: string;
  created_at: string;
  image: ImageOut | null;
  tags: TagOut[];
  analysis: AnalysisData | null;
}

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`请求失败 ${res.status}`);
  return res.json();
}

export const api = {
  analyze: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch("/api/analyze", { method: "POST", body: fd }).then((r) =>
      j<CaseOut>(r)
    );
  },
  cases: (q = "", tag = "") => {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (tag) p.set("tag", tag);
    return fetch(`/api/cases?${p.toString()}`, { cache: "no-store" }).then((r) =>
      j<CaseOut[]>(r)
    );
  },
  case: (id: number | string) =>
    fetch(`/api/cases/${id}`, { cache: "no-store" }).then((r) => j<CaseOut>(r)),
  tags: () =>
    fetch(`/api/tags`, { cache: "no-store" }).then((r) =>
      j<{ id: number; name: string; category: string; count: number }[]>(r)
    ),
  recommend: (text: string, industry = "") =>
    fetch(`/api/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, industry }),
    }).then((r) =>
      j<{
        directions: string[];
        recommended_tags: string[];
        reference_case_ids: number[];
        prompt: string;
      }>(r)
    ),
};
