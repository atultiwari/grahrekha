import { describe, expect, it } from "vitest";
import { EngineError } from "../src/server/engine-client";
import { buildHealthReport } from "../src/server/health-report";

describe("health report", () => {
  it("is healthy when the engine responds", async () => {
    const report = await buildHealthReport({ health: async () => ({ status: "ok", version: "0.1.0" }) });
    expect(report).toEqual({ httpStatus: 200, body: { web: "ok", engine: { status: "ok", version: "0.1.0" } } });
  });

  it("degrades to 503 without leaking error details when the engine is down", async () => {
    const report = await buildHealthReport({
      health: async () => {
        throw new EngineError("engine unreachable: ECONNREFUSED 10.0.0.5", 503);
      },
    });
    expect(report).toEqual({ httpStatus: 503, body: { web: "ok", engine: { status: "unavailable" } } });
  });

  it("reports misconfiguration as 500", async () => {
    const report = await buildHealthReport(() => {
      throw new Error("Invalid server configuration");
    });
    expect(report.httpStatus).toBe(500);
    expect(report.body.engine).toEqual({ status: "misconfigured" });
  });
});
