import { loadServerConfig } from "@/server/config";
import { createEngineClient } from "@/server/engine-client";
import { handleLabPalm, isLabEnabled } from "@/server/lab";

export async function POST(request: Request) {
  if (!isLabEnabled()) return new Response("Not found", { status: 404 });
  const config = loadServerConfig();
  const engine = createEngineClient({ baseUrl: config.engineUrl, secret: config.engineSecret });
  const result = await handleLabPalm(await request.formData(), engine);
  return Response.json(result.body, { status: result.status });
}
