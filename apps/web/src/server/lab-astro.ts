import type { AstroChartV1, BirthDataV1, PlacesResponseV1 } from "@grahrekha/contracts";
import { z } from "zod";
import { EngineError, type EngineClient } from "./engine-client";

const MAX_QUERY_LENGTH = 100;
const PLACE_RESULTS = 8;

type LabAstroEngine = Pick<EngineClient, "searchPlaces" | "astroChart">;

export interface LabAstroResult<T> {
  status: number;
  body: T | { error: string };
}

const BirthFormSchema = z
  .object({
    birth_date: z.string().date("Enter a valid birth date."),
    birth_time: z
      .string()
      .regex(/^(\d{2}:\d{2}(:\d{2})?)?$/, "Enter the time as HH:MM.")
      .default(""),
    time_confidence: z.enum(["exact", "approximate", "unknown"]),
    latitude: z.number().gte(-90).lte(90),
    longitude: z.number().gte(-180).lte(180),
    timezone: z.string().min(1).max(64).nullish(),
  })
  .refine((b) => (b.birth_time === "") === (b.time_confidence === "unknown"), {
    message: "Give a birth time with 'exact' or 'approximate', or leave it empty with 'unknown'.",
  });

function toBirthData(form: z.infer<typeof BirthFormSchema>): BirthDataV1 {
  const time = form.birth_time === "" ? null : form.birth_time.length === 5 ? `${form.birth_time}:00` : form.birth_time;
  return {
    birth_date: form.birth_date,
    birth_time: time,
    time_confidence: form.time_confidence,
    latitude: form.latitude,
    longitude: form.longitude,
    timezone: form.timezone ?? null,
  };
}

function engineFailure(error: unknown): { status: number; body: { error: string } } {
  if (!(error instanceof EngineError)) throw error;
  console.error("[lab] engine error:", error.message);
  const status = error.status >= 400 && error.status < 500 ? error.status : 503;
  return { status, body: { error: error.userMessage ?? "The astrology service is unavailable. Try again." } };
}

export async function handleLabPlaces(
  query: string | null,
  engine: LabAstroEngine,
): Promise<LabAstroResult<PlacesResponseV1>> {
  const q = (query ?? "").trim();
  if (q.length === 0 || q.length > MAX_QUERY_LENGTH) {
    return { status: 400, body: { error: "Type 1-100 characters of a place name." } };
  }
  try {
    return { status: 200, body: await engine.searchPlaces(q, PLACE_RESULTS) };
  } catch (error) {
    return engineFailure(error);
  }
}

export async function handleLabChart(
  body: unknown,
  engine: LabAstroEngine,
  today: Date = new Date(),
): Promise<LabAstroResult<AstroChartV1>> {
  const parsed = BirthFormSchema.safeParse(body);
  if (!parsed.success) {
    return { status: 400, body: { error: parsed.error.issues[0]?.message ?? "Invalid birth details." } };
  }
  // The lab uses today's (UTC) date for the "current" dasha; stored readings will pin it.
  const referenceDate = today.toISOString().slice(0, 10);
  try {
    return { status: 200, body: await engine.astroChart(toBirthData(parsed.data), referenceDate) };
  } catch (error) {
    return engineFailure(error);
  }
}
