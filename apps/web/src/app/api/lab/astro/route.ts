import { loadServerConfig } from "@/server/config";
import { createEngineClient } from "@/server/engine-client";
import { isLabEnabled } from "@/server/lab";
import { handleLabChart } from "@/server/lab-astro";

export async function POST(request: Request) {
  if (!isLabEnabled()) return new Response("Not found", { status: 404 });
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Send the birth details as JSON." }, { status: 400 });
  }
  const config = loadServerConfig();
  const engine = createEngineClient({ baseUrl: config.engineUrl, secret: config.engineSecret });
  const result = await handleLabChart(body, engine);
  return Response.json(result.body, { status: result.status });
}
