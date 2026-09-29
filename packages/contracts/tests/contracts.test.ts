import { describe, expect, it } from "vitest";
import { HealthResponseV1Schema, type HealthResponseV1 } from "../src";
import { buildIndex, exportName, inlineRefs, stripNestedTitles } from "../scripts/gen";
import { PalmAnalysisV1Schema } from "../src";

describe("generated contracts", () => {
  it("validates a well-formed health response", () => {
    const value: HealthResponseV1 = { status: "ok", version: "0.1.0" };
    expect(HealthResponseV1Schema.parse(value)).toEqual(value);
  });

  it("rejects unknown fields and wrong literals (extra=forbid in Pydantic)", () => {
    expect(() => HealthResponseV1Schema.parse({ status: "ok", version: "1", extra: 1 })).toThrow();
    expect(() => HealthResponseV1Schema.parse({ status: "down", version: "1" })).toThrow();
  });

  it("derives export names from versioned contract names", () => {
    expect(exportName("health_response.v1")).toBe("HealthResponseV1");
    expect(exportName("palm_features.v1")).toBe("PalmFeaturesV1");
  });

  it("keeps only the root title so generated aliases never collide across contracts", () => {
    const input = {
      title: "HealthResponse",
      properties: { status: { title: "Status", type: "string" }, tags: { items: [{ title: "T" }] } },
    };
    expect(stripNestedTitles(input)).toEqual({
      title: "HealthResponse",
      properties: { status: { type: "string" }, tags: { items: [{}] } },
    });
  });

  it("re-exports a shared model only once across contracts", () => {
    const a = "export interface Shared {}\nexport interface A {}\nexport const ASchema = 1";
    const b = "export interface Shared {}\nexport interface B {}";
    expect(buildIndex([{ module: "a.v1", source: a }, { module: "b.v1", source: b }])).toBe(
      'export type { Shared, A } from "./a.v1";\nexport { ASchema } from "./a.v1";\nexport type { B } from "./b.v1";',
    );
  });

  it("inlines $defs so nested models are validated, not z.any()", () => {
    const schema = { $defs: { Inner: { type: "object", properties: { n: { type: "number" } } } },
      properties: { inner: { $ref: "#/$defs/Inner" } } };
    expect(inlineRefs(schema)).toEqual({ properties: { inner: { type: "object", properties: { n: { type: "number" } } } } });
  });

  it("the generated palm analysis validator rejects malformed nested data", () => {
    const bad = { schema_version: "palm_analysis.v1", gate: { passed: "yes" }, features: null, overlay: null, feature_hash: null };
    expect(PalmAnalysisV1Schema.safeParse(bad).success).toBe(false);
  });
});
