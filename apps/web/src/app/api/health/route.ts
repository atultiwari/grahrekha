import { loadServerConfig } from "@/server/config";
import { createEngineClient } from "@/server/engine-client";
import { buildHealthReport } from "@/server/health-report";

export async function GET() {
  const report = await buildHealthReport(() => {
    const config = loadServerConfig();
    return createEngineClient({ baseUrl: config.engineUrl, secret: config.engineSecret });
  });
  return Response.json(report.body, { status: report.httpStatus });
}
