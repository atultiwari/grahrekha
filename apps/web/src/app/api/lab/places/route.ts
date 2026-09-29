import { loadServerConfig } from "@/server/config";
import { createEngineClient } from "@/server/engine-client";
import { isLabEnabled } from "@/server/lab";
import { handleLabPlaces } from "@/server/lab-astro";

export async function GET(request: Request) {
  if (!isLabEnabled()) return new Response("Not found", { status: 404 });
  const config = loadServerConfig();
  const engine = createEngineClient({ baseUrl: config.engineUrl, secret: config.engineSecret });
  const result = await handleLabPlaces(new URL(request.url).searchParams.get("q"), engine);
  return Response.json(result.body, { status: result.status });
}
