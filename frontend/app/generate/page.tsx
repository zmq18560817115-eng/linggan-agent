"use client";
import { useState } from "react";
import Link from "next/link";
import { api, RecommendResult } from "@/lib/api";
import { Card, Swatches, Tag } from "@/components/ui";

export default function GeneratePage() {
  const [text, setText] = useState("");
  const [industry, setIndustry] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<RecommendResult | null>(null);
  const [copied, setCopied] = useState(false);

  const onPick = (f: File | null) => {
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : "");
  };

  const run = async () => {
    if (!text.trim() && !file) return;
    setLoading(true);
    try {
      setRes(await api.recommend(text, industry, file));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold">需求视觉方向推荐</h1>
      <p className="mb-6 text-sm text-gray-400">
        上传<span className="text-indigo-400">意向图</span>并/或输入需求描述，系统会先解析意向图的视觉特征，
        再结合案例知识库推荐视觉方向、风格标签与可直接用于生图的 AI 提示词（对应方案「未来升级 V3.0」雏形）。
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          {/* 意向图上传 */}
          <label className="text-sm text-gray-400">意向图 / 参考图（可选）</label>
          <label className="mt-1 flex h-40 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-line hover:border-indigo-500">
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="意向图" className="max-h-36 rounded-md" />
            ) : (
              <span className="text-sm text-gray-500">点击上传意向图 · PNG / JPG</span>
            )}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => onPick(e.target.files?.[0] || null)}
            />
          </label>
          {file && (
            <button
              onClick={() => onPick(null)}
              className="mt-1 text-xs text-gray-500 underline"
            >
              移除意向图
            </button>
          )}

          <label className="mt-4 block text-sm text-gray-400">需求描述</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="例如：想要一个科技感强、简约高端的产品官网首屏"
            className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 outline-none focus:border-indigo-500"
          />
          <label className="mt-3 block text-sm text-gray-400">行业（可选）</label>
          <input
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="互联网 / 美妆 / 餐饮…"
            className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 outline-none focus:border-indigo-500"
          />
          <button
            onClick={run}
            disabled={loading || (!text.trim() && !file)}
            className="mt-4 w-full rounded-lg bg-indigo-500 py-2.5 font-medium hover:bg-indigo-400 disabled:opacity-40"
          >
            {loading ? "推荐中…" : "生成视觉方向"}
          </button>
          <p className="mt-2 text-xs text-gray-500">意向图与描述至少填一项。</p>
        </Card>

        <div className="space-y-4">
          {!res ? (
            <Card>
              <p className="text-sm text-gray-500">推荐结果会显示在这里。</p>
            </Card>
          ) : (
            <>
              {res.has_reference && (
                <Card className="border-indigo-500/40">
                  <div className="mb-2 text-sm font-semibold text-indigo-300">
                    意向图解析
                  </div>
                  <div className="flex gap-3">
                    {preview && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={preview}
                        alt="意向图"
                        className="h-20 w-20 rounded-md object-cover"
                      />
                    )}
                    <div className="flex-1">
                      <div className="mb-1 flex flex-wrap gap-1.5">
                        {res.reference_style.map((s) => (
                          <Tag key={s}>{s}</Tag>
                        ))}
                      </div>
                      <Swatches colors={res.reference_palette.slice(0, 5)} />
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-gray-400">
                    版式：{res.reference_layout} · 字体：{res.reference_font}
                  </p>
                  {res.reference_summary && (
                    <p className="mt-1 text-xs text-gray-500">{res.reference_summary}</p>
                  )}
                </Card>
              )}

              <Card>
                <div className="mb-2 text-sm font-semibold text-gray-300">推荐视觉方向</div>
                <ul className="list-disc space-y-1 pl-5 text-sm text-gray-300">
                  {res.directions.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {res.recommended_tags.map((t) => (
                    <Tag key={t}>{t}</Tag>
                  ))}
                </div>
              </Card>

              <Card>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-300">
                    推荐 AI 绘图提示词
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(res.prompt);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 1500);
                    }}
                    className="text-xs text-indigo-400 hover:underline"
                  >
                    {copied ? "已复制" : "复制"}
                  </button>
                </div>
                <pre className="whitespace-pre-wrap rounded-lg bg-ink p-3 text-xs text-gray-300">
                  {res.prompt}
                </pre>
              </Card>

              {res.reference_case_ids.length > 0 && (
                <Card>
                  <div className="mb-2 text-sm font-semibold text-gray-300">参考案例</div>
                  <div className="flex flex-wrap gap-2">
                    {res.reference_case_ids.map((id) => (
                      <Link
                        key={id}
                        href={`/cases/${id}`}
                        className="text-sm text-indigo-400 hover:underline"
                      >
                        案例 #{id}
                      </Link>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
