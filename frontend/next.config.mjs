/** @type {import('next').NextConfig} */

// 默认部署在 Firebase Hosting 站点根路径，basePath 留空。
// 改部署到 GitHub Pages 这类 /<repo> 子路径站点时，构建前设 PAGES_BASE_PATH（如 "/ai-radar"）。
const basePath = process.env.PAGES_BASE_PATH || "";

const nextConfig = {
  // 静态导出：产出纯静态 HTML/CSS/JS 到 out/，由 firebase.json 指向它托管
  output: "export",
  basePath,
  // 让客户端代码能读到 basePath（用于 RSS 等手写链接前缀）
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  images: {
    // 静态导出不支持 Next 图片优化服务
    unoptimized: true,
  },
  // 目录式路由（/feed/ → /feed/index.html），与 firebase.json 的 trailingSlash 对应
  trailingSlash: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
