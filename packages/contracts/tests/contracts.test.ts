import { describe, expect, it } from "vitest";
import { HealthResponseV1Schema, type HealthResponseV1 } from "../src";
import { exportName, stripNestedTitles } from "../scripts/gen";

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
});
