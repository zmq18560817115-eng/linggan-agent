"use client";
import { useEffect, useState } from "react";
import { api, ConceptData, DistItem } from "@/lib/api";
import { Card, Tag } from "@/components/ui";

function Bars({ items }: { items: DistItem[] }) {
  if (!items || items.length === 0)
    return <p className="text-xs text-gray-500">暂无数据</p>;
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <div className="space-y-1.5">
      {items.map((i) => (
        <div key={i.name} className="flex items-center gap-2 text-xs">
          <div className="w-28 shrink-0 truncate text-gray-400" title={i.name}>
            {i.name}
          </div>
          <div className="h-4 flex-1 rounded bg-ink">
            <div
              className="h-4 rounded bg-indigo-500/70"
              style={{ width: `${(i.count / max) * 100}%` }}
            />
          </div>
          <div className="w-10 shrink-0 text-right text-gray-500">{i.pct}%</div>
        </div>
      ))}
    </div>
  );
}

function MiniMarkdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const render = (s: string) =>
    s.split(/(\*\*[^*]+\*\*)/g).map((seg, i) =>
      seg.startsWith("**") && seg.endsWith("**") ? (
        <strong key={i} className="text-gray-100">
          {seg.slice(2, -2)}
        </strong>
      ) : (
        <span key={i}>{seg}</span>
      )
    );
  return (
    <div className="space-y-1.5 text-sm text-gray-300">
      {lines.map((ln, i) => {
        if (/^###\s/.test(ln))
          return <h4 key={i} className="mt-3 font-semibold text-gray-200">{render(ln.replace(/^###\s/, ""))}</h4>;
        if (/^##\s/.test(ln))
          return <h3 key={i} className="mt-4 text-base font-semibold text-indigo-300">{render(ln.replace(/^##\s/, ""))}</h3>;
        if (/^#\s/.test(ln))
          return <h2 key={i} className="mt-2 text-lg font-bold">{render(ln.replace(/^#\s/, ""))}</h2>;
        if (/^[-*]\s/.test(ln))
          return <li key={i} className="ml-5 list-disc">{render(ln.replace(/^[-*]\s/, ""))}</li>;
        if (ln.trim() === "") return <div key={i} className="h-1" />;
        return <p key={i}>{render(ln)}</p>;
      })}
    </div>
  );
}

export default function ConceptPage() {
  const [d, setD] = useState<ConceptData | null>(null);
  const [err, setErr] = useState("");
  const [methodology, setMethodology] = useState("");
  const [mLoading, setMLoading] = useState(false);
  const [mNote, setMNote] = useState("");

  const genMethodology = async () => {
    setMLoading(true);
    setMNote("");
    try {
      const r = await api.methodology();
      if (!r.enabled) {
        setMNote("未配置文本大模型（LLM_*）。在后端设置 LLM_API_KEY 与 LLM_MODEL 后即可生成。");
      } else if (!r.methodology) {
        setMNote(r.note || "暂无法生成。");
      } else {
        setMethodology(r.methodology);
      }
    } catch {
      setMNote("生成失败，请稍后重试或检查模型配置。");
    } finally {
      setMLoading(false);
    }
  };

  useEffect(() => {
    api
      .concept()
      .then(setD)
      .catch(() => setErr("加载失败，请确认后端已启动。"));
  }, []);

  if (err) return <p className="text-gray-500">{err}</p>;
  if (!d) return <p className="text-gray-500">加载中…</p>;

  const dist = d.distributions;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">设计视觉概论</h1>
        <p className="mt-1 text-sm text-gray-400">
          从 {d.total} 个案例中沉淀出的团队专属设计规律——随案例增多自我进化。
        </p>
        {!d.enough && (
          <div className="mt-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
            当前素材 {d.total} 个，建议积累到 {d.threshold} 个以上，概论会更可信。多去「AI拆解」上传案例吧。
          </div>
        )}
      </div>

      {d.total === 0 ? (
        <Card>
          <p className="text-sm text-gray-500">
            还没有案例。前往「AI拆解」上传图片，系统会自动沉淀设计规律。
          </p>
        </Card>
      ) : (
        <>
          {/* AI 设计方法论 */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">AI 设计方法论</h2>
              <button
                onClick={genMethodology}
                disabled={mLoading}
                className="rounded-lg bg-indigo-500 px-4 py-1.5 text-sm font-medium hover:bg-indigo-400 disabled:opacity-40"
              >
                {mLoading
                  ? "生成中…（约 1~2 分钟）"
                  : methodology
                  ? "重新生成"
                  : "AI 生成设计方法论"}
              </button>
            </div>
            {mNote && (
              <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
                {mNote}
              </div>
            )}
            {methodology && (
              <Card>
                <MiniMarkdown text={methodology} />
              </Card>
            )}
            {!methodology && !mNote && (
              <p className="text-sm text-gray-500">
                点击右上角，用大模型把下面的数据写成一份团队专属、成体系的设计方法论。
              </p>
            )}
          </section>

          {/* 提炼的设计原则 */}
          <section>
            <h2 className="mb-3 text-lg font-semibold">提炼的设计原则</h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {d.principles.map((p, i) => (
                <Card key={i} className="border-indigo-500/40">
                  <div className="flex gap-2">
                    <span className="text-indigo-400">#{i + 1}</span>
                    <span className="text-sm text-gray-200">{p}</span>
                  </div>
                </Card>
              ))}
            </div>
          </section>

          {/* 视觉 DNA */}
          <section>
            <h2 className="mb-3 text-lg font-semibold">团队视觉 DNA</h2>
            <Card>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <div className="text-xs text-gray-500">最常用版式</div>
                  <div className="mt-1 text-sm font-medium">{d.visual_dna.top_layout || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">标志性风格</div>
                  <div className="mt-1 text-sm font-medium">{d.visual_dna.top_style || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">常用栅格</div>
                  <div className="mt-1 text-sm font-medium">{d.visual_dna.top_grid || "—"}</div>
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-500">高频主色</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {d.visual_dna.colors.map((c) => (
                  <div key={c.hex} className="flex items-center gap-1.5">
                    <div
                      className="h-8 w-8 rounded-md border border-line"
                      style={{ backgroundColor: c.hex }}
                      title={`${c.hex} ×${c.count}`}
                    />
                  </div>
                ))}
              </div>
            </Card>
          </section>

          {/* 分布画像 */}
          <section>
            <h2 className="mb-3 text-lg font-semibold">分布画像</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {[
                ["版式类型", dist.layout],
                ["风格标签", dist.style],
                ["栅格结构", dist.grid],
                ["色彩色系", dist.color_family],
                ["行业分布", dist.industry],
                ["字体调性", dist.font],
              ].map(([label, items]) => (
                <Card key={label as string}>
                  <div className="mb-2 text-sm font-semibold text-gray-300">
                    {label as string}
                  </div>
                  <Bars items={items as DistItem[]} />
                </Card>
              ))}
            </div>
          </section>

          {/* 分行业概论 */}
          {d.by_industry.length > 0 && (
            <section>
              <h2 className="mb-3 text-lg font-semibold">分行业概论</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {d.by_industry.map((b) => (
                  <Card key={b.industry}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{b.industry}</span>
                      <span className="text-xs text-gray-500">{b.count} 例</span>
                    </div>
                    <p className="mt-2 text-sm text-gray-300">{b.principle}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {b.top_styles.map((s) => (
                        <Tag key={s}>{s}</Tag>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
