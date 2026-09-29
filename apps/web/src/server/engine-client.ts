import { HealthResponseV1Schema, type HealthResponseV1 } from "@grahrekha/contracts";
import type { ZodType } from "zod";

/** Raised for any failure talking to the engine; `status` mirrors the HTTP status to return. */
export class EngineError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "EngineError";
  }
}

export interface EngineClientOptions {
  baseUrl: string;
  secret: string;
  fetchFn?: typeof fetch;
  timeoutMs?: number;
}

export function createEngineClient({ baseUrl, secret, fetchFn = fetch, timeoutMs = 10_000 }: EngineClientOptions) {
  const root = baseUrl.replace(/\/+$/, "");

  async function request<T>(path: string, schema: ZodType<T>): Promise<T> {
    let response: Response;
    try {
      response = await fetchFn(`${root}${path}`, {
        headers: { "X-Engine-Secret": secret, accept: "application/json" },
        signal: AbortSignal.timeout(timeoutMs),
        cache: "no-store",
      });
    } catch (cause) {
      throw new EngineError(`engine unreachable: ${(cause as Error).message}`, 503);
    }
    if (!response.ok) {
      throw new EngineError(`engine returned ${response.status} for ${path}`, response.status);
    }
    const parsed = schema.safeParse(await response.json());
    if (!parsed.success) {
      throw new EngineError(`engine response for ${path} broke the contract`, 502);
    }
    return parsed.data;
  }

  return {
    health: (): Promise<HealthResponseV1> => request("/healthz", HealthResponseV1Schema),
  };
}
