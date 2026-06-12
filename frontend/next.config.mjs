/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // 构建期不因 lint 失败（项目未引入 eslint 配置）
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
