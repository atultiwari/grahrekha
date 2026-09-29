import type { PalmAnalysisV1, RulesResponseV1 } from "@grahrekha/contracts";
import { EngineError, type DeclaredHand, type EngineClient } from "./engine-client";

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

/**
 * The lab shows UNREVIEWED rules (D-008), so it is on by default only in development.
 * A public deployment must opt in explicitly with LAB_ENABLED=true.
 */
export function isLabEnabled(env: Record<string, string | undefined> = process.env): boolean {
  return env.LAB_ENABLED === "true" || env.NODE_ENV !== "production";
}

export interface LabResult {
  status: number;
  body: { analysis: PalmAnalysisV1; rules: RulesResponseV1 | null } | { error: string };
}

type LabEngine = Pick<EngineClient, "analyzePalm" | "evaluateRules">;

export async function handleLabPalm(form: FormData, engine: LabEngine): Promise<LabResult> {
  const file = form.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { status: 400, body: { error: "Choose a palm photo to upload." } };
  }
  if (!file.type.startsWith("image/")) {
    return { status: 415, body: { error: "Please upload an image (JPEG, PNG or HEIC)." } };
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return { status: 413, body: { error: "This photo is too large (max 20 MB)." } };
  }
  const hand = form.get("declared_hand");
  if (hand !== null && hand !== "" && hand !== "left" && hand !== "right") {
    return { status: 400, body: { error: "Hand must be left or right." } };
  }
  const declaredHand: DeclaredHand = hand === "left" || hand === "right" ? hand : null;

  try {
    const analysis = await engine.analyzePalm(file, file.name || "palm.jpg", declaredHand);
    const rules = analysis.features ? await engine.evaluateRules(analysis.features, true) : null;
    return { status: 200, body: { analysis, rules } };
  } catch (error) {
    if (error instanceof EngineError) {
      console.error("[lab] engine error:", error.message);
      const status = error.status >= 400 && error.status < 500 ? error.status : 502;
      return { status, body: { error: error.userMessage ?? "The analysis service is unavailable. Try again." } };
    }
    throw error;
  }
}
