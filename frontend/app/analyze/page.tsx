"use client";
import { useState } from "react";
import Link from "next/link";
import { api, CaseOut } from "@/lib/api";
import { Card, Swatches, Tag } from "@/components/ui";

export default function AnalyzePage() {
  const [preview, setPreview] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CaseOut | null>(null);
  const [error, setError] = useState("");

  const onPick = (f: File | null) => {
    setResult(null);
    setError("");
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : "");
  };

  const run = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      setResult(await api.analyze(file));
    } catch (e) {
      setError("分析失败，请确认后端服务已启动。");
    } finally {
      setLoading(false);
    }
  };

  const a = result?.analysis;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold">AI 视觉拆解</h1>
      <p className="mb-6 text-sm text-gray-400">
        上传一张优秀案例图片，AI Agent 流水线（Vision → Style → Design → Rule →
        Prompt）会自动生成结构化的设计拆解报告与案例资产卡。
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <label className="flex h-64 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-line hover:border-indigo-500">
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="预览" className="max-h-60 rounded-md" />
            ) : (
              <span className="text-gray-500">点击选择图片 · PNG / JPG</span>
            )}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => onPick(e.target.files?.[0] || null)}
            />
          </label>
          <button
            onClick={run}
            disabled={!file || loading}
            className="mt-4 w-full rounded-lg bg-indigo-500 py-2.5 font-medium hover:bg-indigo-400 disabled:opacity-40"
          >
            {loading ? "AI 分析中…" : "开始拆解"}
          </button>
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        </Card>

        <div className="space-y-4">
          {!result && (
            <Card>
              <p className="text-sm text-gray-500">
                分析结果会显示在这里：视觉风格、色彩体系、构图、光影、材质、设计规则与
                AI 绘图提示词。
              </p>
            </Card>
          )}

          {result && a && (
            <>
              <Card>
                <div className="text-lg font-semibold">{result.name}</div>
                <p className="mt-1 text-sm text-gray-400">{result.summary}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {result.tags.map((t) => (
                    <Tag key={t.id}>{t.name}</Tag>
                  ))}
                </div>
                <Link
                  href={`/cases/${result.id}`}
                  className="mt-4 inline-block text-sm text-indigo-400 hover:underline"
                >
                  查看完整案例卡 →
                </Link>
              </Card>

              <Card>
                <div className="mb-2 text-sm font-semibold text-gray-300">色彩体系</div>
                <Swatches colors={a.color.palette} />
                <p className="mt-2 text-xs text-gray-500">{a.color.description}</p>
              </Card>

              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <div className="text-sm font-semibold text-gray-300">构图</div>
                  <div className="mt-1 text-sm">{a.composition.type}</div>
                  <p className="mt-1 text-xs text-gray-500">{a.composition.description}</p>
                </Card>
                <Card>
                  <div className="text-sm font-semibold text-gray-300">光影</div>
                  <div className="mt-1 text-sm">{a.light.type}</div>
                  <p className="mt-1 text-xs text-gray-500">{a.light.description}</p>
                </Card>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
