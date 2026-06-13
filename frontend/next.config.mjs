/** @type {import('next').NextConfig} */

// GitHub Pages 项目站点部署在 /<repo> 子路径下，需要 basePath。
// 本地预览时 PAGES_BASE_PATH 留空即可（根路径）。CI 里设为 "/ai-radar"。
const basePath = process.env.PAGES_BASE_PATH || "";

const nextConfig = {
  // 静态导出：产出纯静态 HTML/CSS/JS 到 out/，可直接托管到 GitHub Pages
  output: "export",
  basePath,
  // 让客户端代码能读到 basePath（用于 RSS 等手写链接前缀）
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  images: {
    // 静态导出不支持 Next 图片优化服务
    unoptimized: true,
  },
  // 目录式路由，Pages 友好（/feed/ → /feed/index.html）
  trailingSlash: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
