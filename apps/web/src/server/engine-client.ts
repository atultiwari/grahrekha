import {
  AstroChartV1Schema,
  HealthResponseV1Schema,
  PalmAnalysisV1Schema,
  PlacesResponseV1Schema,
  RulesResponseV1Schema,
  type AstroChartV1,
  type BirthDataV1,
  type HealthResponseV1,
  type PalmAnalysisV1,
  type PalmFeaturesV1,
  type PlacesResponseV1,
  type RulesResponseV1,
} from "@grahrekha/contracts";
import type { ZodType, ZodTypeDef } from "zod";

/** Raised for any failure talking to the engine; `status` mirrors the HTTP status to return. */
export class EngineError extends Error {
  constructor(
    message: string,
    readonly status: number,
    /** Safe to show to users (the engine's own 4xx message), when available. */
    readonly userMessage?: string,
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

export type DeclaredHand = "left" | "right" | null;

async function readDetail(response: Response): Promise<string | undefined> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : undefined;
  } catch {
    return undefined;
  }
}

export function createEngineClient({ baseUrl, secret, fetchFn = fetch, timeoutMs = 10_000 }: EngineClientOptions) {
  const root = baseUrl.replace(/\/+$/, "");

  async function request<T>(
    path: string,
    // Input is unknown: schemas with .default() have optional inputs but complete outputs.
    schema: ZodType<T, ZodTypeDef, unknown>,
    init: { method?: string; body?: BodyInit; headers?: Record<string, string>; timeoutMs?: number } = {},
  ): Promise<T> {
    let response: Response;
    try {
      response = await fetchFn(`${root}${path}`, {
        method: init.method ?? "GET",
        body: init.body,
        headers: { "X-Engine-Secret": secret, accept: "application/json", ...init.headers },
        signal: AbortSignal.timeout(init.timeoutMs ?? timeoutMs),
        cache: "no-store",
      });
    } catch (cause) {
      throw new EngineError(`engine unreachable: ${(cause as Error).message}`, 503);
    }
    if (!response.ok) {
      const detail = response.status >= 400 && response.status < 500 ? await readDetail(response) : undefined;
      throw new EngineError(`engine returned ${response.status} for ${path}`, response.status, detail);
    }
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw new EngineError(`engine returned non-JSON for ${path}`, 502);
    }
    const parsed = schema.safeParse(body);
    if (!parsed.success) {
      throw new EngineError(`engine response for ${path} broke the contract`, 502);
    }
    return parsed.data;
  }

  return {
    health: (): Promise<HealthResponseV1> => request("/healthz", HealthResponseV1Schema),

    analyzePalm: (photo: Blob, filename: string, declaredHand: DeclaredHand): Promise<PalmAnalysisV1> => {
      const form = new FormData();
      form.set("file", photo, filename);
      if (declaredHand) form.set("declared_hand", declaredHand);
      return request("/v1/palm/analyze", PalmAnalysisV1Schema, { method: "POST", body: form, timeoutMs: 30_000 });
    },

    evaluateRules: (features: PalmFeaturesV1, includeUnreviewed: boolean): Promise<RulesResponseV1> =>
      request("/v1/rules/evaluate", RulesResponseV1Schema, {
        method: "POST",
        body: JSON.stringify({ features, include_unreviewed: includeUnreviewed }),
        headers: { "content-type": "application/json" },
      }),

    searchPlaces: (query: string, limit: number): Promise<PlacesResponseV1> => {
      const params = new URLSearchParams({ q: query, limit: String(limit) });
      return request(`/v1/places?${params.toString()}`, PlacesResponseV1Schema);
    },

    /** `referenceDate` (YYYY-MM-DD) fixes which dasha is "current", keeping results reproducible. */
    astroChart: (birth: BirthDataV1, referenceDate: string): Promise<AstroChartV1> =>
      request("/v1/astro/chart", AstroChartV1Schema, {
        method: "POST",
        body: JSON.stringify({ birth, reference_date: referenceDate }),
        headers: { "content-type": "application/json" },
        timeoutMs: 30_000,
      }),
  };
}

export type EngineClient = ReturnType<typeof createEngineClient>;
