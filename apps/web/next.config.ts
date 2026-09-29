import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server for Docker (docker-compose.yml). Tracing starts at the
  // monorepo root so workspace packages are included.
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, "../../"),
  // Workspace packages ship TypeScript source.
  transpilePackages: ["@grahrekha/contracts"],
};

export default nextConfig;
