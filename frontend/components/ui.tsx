import Link from "next/link";
import { ReactNode } from "react";
import { CaseOut } from "@/lib/api";

export function Nav() {
  const items = [
    { href: "/", label: "首页" },
    { href: "/cases", label: "案例库" },
    { href: "/analyze", label: "AI拆解" },
    { href: "/batch", label: "批量上传" },
    { href: "/concept", label: "设计概论" },
    { href: "/generate", label: "需求生成" },
  ];
  return (
    <nav className="sticky top-0 z-10 border-b border-line bg-ink/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid h-7 w-7 place-items-center rounded bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-sm">
            灵
          </span>
          AI视觉拆解 Agent
        </Link>
        <div className="flex gap-1 text-sm">
          {items.map((i) => (
            <Link
              key={i.href}
              href={i.href}
              className="rounded-md px-3 py-1.5 text-gray-300 hover:bg-panel hover:text-white"
            >
              {i.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full border border-line bg-panel px-2.5 py-0.5 text-xs text-gray-300">
      {children}
    </span>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-line bg-panel p-5 ${className}`}>
      {children}
    </div>
  );
}

export function CaseCard({ c }: { c: CaseOut }) {
  return (
    <Link href={`/cases/${c.id}`}>
      <div className="group overflow-hidden rounded-xl border border-line bg-panel transition hover:border-indigo-500">
        {c.image && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={c.image.url} alt={c.name} className="h-44 w-full object-cover" />
        )}
        <div className="p-4">
          <div className="font-medium group-hover:text-indigo-400">{c.name}</div>
          <div className="mt-1 line-clamp-2 text-xs text-gray-500">{c.summary}</div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {c.tags.slice(0, 4).map((t) => (
              <Tag key={t.id}>{t.name}</Tag>
            ))}
          </div>
        </div>
      </div>
    </Link>
  );
}

export function Swatches({ colors }: { colors: string[] }) {
  return (
    <div className="flex gap-1.5">
      {colors.map((c) => (
        <div
          key={c}
          title={c}
          className="h-8 w-8 rounded-md border border-line"
          style={{ backgroundColor: c }}
        />
      ))}
    </div>
  );
}
