import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/ui";

export const metadata: Metadata = {
  title: "AI视觉拆解 Agent",
  description: "优秀案例图片 → AI视觉理解 → 设计拆解 → 案例资产卡 → 团队复用",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <Nav />
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="border-t border-line py-8 text-center text-xs text-gray-500">
          AI视觉知识资产平台 · MVP V1.0
        </footer>
      </body>
    </html>
  );
}
