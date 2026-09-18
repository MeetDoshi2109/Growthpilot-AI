import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Rewrites API calls to the backend (local dev)
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/:path*`,
      },
    ];
  },
  // For Vercel + Railway/Render deployment
  // Frontend on Vercel, backend on Railway
  env: {
    NEXT_PUBLIC_APP_NAME: "GrowthPilot AI",
    NEXT_PUBLIC_SANDBOX: "true",
  },
};

export default nextConfig;
