/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 便于容器化部署：产出自包含的 standalone 输出
  output: "standalone",
  async rewrites() {
    // 将 /api 与 /uploads 代理到 FastAPI 后端，避免跨域配置
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
      { source: "/uploads/:path*", destination: `${backend}/uploads/:path*` },
    ];
  },
};

module.exports = nextConfig;
