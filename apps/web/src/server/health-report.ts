import type { HealthResponseV1 } from "@grahrekha/contracts";

type EngineHealth = HealthResponseV1 | { status: "unavailable" } | { status: "misconfigured" };

export interface HealthReport {
  httpStatus: 200 | 500 | 503;
  body: { web: "ok"; engine: EngineHealth };
}

interface HealthSource {
  health(): Promise<HealthResponseV1>;
}

/**
 * Combines web + engine health. Error details are logged server-side only,
 * never returned to the client (they can contain internal hostnames).
 */
export async function buildHealthReport(source: HealthSource | (() => HealthSource)): Promise<HealthReport> {
  let client: HealthSource;
  try {
    client = typeof source === "function" ? source() : source;
  } catch (error) {
    console.error("[health] configuration error:", error);
    return { httpStatus: 500, body: { web: "ok", engine: { status: "misconfigured" } } };
  }
  try {
    return { httpStatus: 200, body: { web: "ok", engine: await client.health() } };
  } catch (error) {
    console.error("[health] engine check failed:", error);
    return { httpStatus: 503, body: { web: "ok", engine: { status: "unavailable" } } };
  }
}
