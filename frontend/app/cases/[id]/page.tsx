"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, CaseOut } from "@/lib/api";
import { Card, Swatches, Tag } from "@/components/ui";

export default function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const [c, setC] = useState<CaseOut | null>(null);
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api
      .case(id)
      .then(setC)
      .catch(() => setErr("案例不存在"));
  }, [id]);

  if (err) return <p className="text-gray-500">{err}</p>;
  if (!c) return <p className="text-gray-500">加载中…</p>;
  const a = c.analysis;

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.1fr_1fr]">
      <div>
        {c.image && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={c.image.url} alt={c.name} className="w-full rounded-xl border border-line" />
        )}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {c.tags.map((t) => (
            <Tag key={t.id}>{t.name}</Tag>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold">{c.name}</h1>
          <p className="mt-1 text-sm text-gray-400">{c.summary}</p>
          <div className="mt-2 text-xs text-gray-500">
            行业：{c.industry} · 场景：{c.scene}
          </div>
        </div>

        {a && (
          <>
            <Card>
              <div className="mb-2 text-sm font-semibold text-gray-300">视觉风格</div>
              <div className="flex flex-wrap gap-1.5">
                {a.style.style_tags.map((s) => (
                  <Tag key={s}>{s}</Tag>
                ))}
              </div>
              <p className="mt-2 text-xs text-gray-500">
                情绪：{a.style.mood_keywords.join("、")} · 品牌定位：
                {a.style.brand_position}
              </p>
            </Card>

            <Card>
              <div className="mb-2 text-sm font-semibold text-gray-300">色彩体系</div>
              <Swatches colors={a.color.palette} />
              <p className="mt-2 text-xs text-gray-500">{a.color.description}</p>
            </Card>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Card>
                <div className="text-xs font-semibold text-gray-400">构图</div>
                <div className="mt-1 text-sm">{a.composition.type}</div>
              </Card>
              <Card>
                <div className="text-xs font-semibold text-gray-400">光影</div>
                <div className="mt-1 text-sm">{a.light.type}</div>
              </Card>
              <Card>
                <div className="text-xs font-semibold text-gray-400">材质</div>
                <div className="mt-1 text-sm">{a.material}</div>
              </Card>
            </div>

            <Card>
              <div className="mb-2 text-sm font-semibold text-gray-300">设计规则</div>
              <div className="text-xs text-gray-400">为什么优秀</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-300">
                {a.design_rules.why_good.map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
              <div className="mt-3 text-xs text-gray-400">可复用方法</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-300">
                {a.design_rules.reusable_methods.map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </Card>

            <Card>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-300">AI 绘图提示词</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(a.prompt);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                  }}
                  className="text-xs text-indigo-400 hover:underline"
                >
                  {copied ? "已复制" : "复制"}
                </button>
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-ink p-3 text-xs text-gray-300">
                {a.prompt}
              </pre>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
