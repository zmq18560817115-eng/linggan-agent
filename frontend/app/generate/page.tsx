"use client";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, Tag } from "@/components/ui";

export default function GeneratePage() {
  const [text, setText] = useState("");
  const [industry, setIndustry] = useState("");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<Awaited<ReturnType<typeof api.recommend>> | null>(
    null
  );

  const run = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      setRes(await api.recommend(text, industry));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold">需求视觉方向推荐</h1>
      <p className="mb-6 text-sm text-gray-400">
        输入你的需求描述，系统结合案例知识库推荐视觉方向、风格标签与可用的 AI
        绘图提示词（对应方案「未来升级 V3.0」雏形）。
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <label className="text-sm text-gray-400">需求描述</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
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
            disabled={loading || !text.trim()}
            className="mt-4 w-full rounded-lg bg-indigo-500 py-2.5 font-medium hover:bg-indigo-400 disabled:opacity-40"
          >
            {loading ? "推荐中…" : "生成视觉方向"}
          </button>
        </Card>

        <div className="space-y-4">
          {!res ? (
            <Card>
              <p className="text-sm text-gray-500">推荐结果会显示在这里。</p>
            </Card>
          ) : (
            <>
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
                <div className="mb-2 text-sm font-semibold text-gray-300">
                  推荐 AI 绘图提示词
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
