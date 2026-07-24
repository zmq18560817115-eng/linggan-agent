"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CaseOut } from "@/lib/api";
import { Card, Tag, CaseCard } from "@/components/ui";

export default function Home() {
  const [cases, setCases] = useState<CaseOut[]>([]);
  const [tags, setTags] = useState<{ name: string; count: number }[]>([]);

  useEffect(() => {
    api.cases().then(setCases).catch(() => {});
    api.tags().then(setTags).catch(() => {});
  }, []);

  return (
    <div className="space-y-10">
      <section className="rounded-2xl border border-line bg-gradient-to-br from-panel to-ink p-10">
        <h1 className="text-3xl font-bold">把优秀案例，沉淀为团队的视觉知识资产</h1>
        <p className="mt-3 max-w-2xl text-gray-400">
          优秀案例图片 → AI视觉理解 → 设计拆解 → 案例资产卡 → 团队复用。
          让设计经验不再依赖个人，把优秀案例转化为可复用的设计规则。
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            href="/analyze"
            className="rounded-lg bg-indigo-500 px-5 py-2.5 font-medium hover:bg-indigo-400"
          >
            上传图片，开始拆解
          </Link>
          <Link
            href="/cases"
            className="rounded-lg border border-line px-5 py-2.5 font-medium hover:bg-panel"
          >
            浏览案例库
          </Link>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold">热门风格</h2>
        {tags.length === 0 ? (
          <p className="text-sm text-gray-500">暂无标签，先去拆解一张图片吧。</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {tags
              .sort((a, b) => b.count - a.count)
              .slice(0, 20)
              .map((t) => (
                <Link key={t.name} href={`/cases?tag=${encodeURIComponent(t.name)}`}>
                  <Tag>
                    {t.name} · {t.count}
                  </Tag>
                </Link>
              ))}
          </div>
        )}
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">案例推荐</h2>
          <Link href="/cases" className="text-sm text-indigo-400 hover:underline">
            查看全部 →
          </Link>
        </div>
        {cases.length === 0 ? (
          <Card>
            <p className="text-sm text-gray-500">
              案例库还是空的。前往「AI拆解」上传第一张图片，系统会自动生成案例资产卡。
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {cases.slice(0, 6).map((c) => (
              <CaseCard key={c.id} c={c} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
