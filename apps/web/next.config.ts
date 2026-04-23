import type { NextConfig } from "next";

const isDesktopBuild = process.env.BUILD_DESKTOP === "1";

const nextConfig: NextConfig = {
  output: isDesktopBuild ? "export" : undefined,
  images: {
    unoptimized: isDesktopBuild,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cdn.freshful.ro",
      },
    ],
  },
};

export default nextConfig;
