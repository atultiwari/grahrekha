import { describe, expect, it } from "vitest";
import { loadServerConfig } from "../src/server/config";

describe("server config", () => {
  it("reads engine settings from the environment", () => {
    const config = loadServerConfig({ ENGINE_URL: "http://localhost:8000", ENGINE_SHARED_SECRET: "x" });
    expect(config).toEqual({ engineUrl: "http://localhost:8000", engineSecret: "x" });
  });

  it("fails fast with a clear message when required settings are missing", () => {
    expect(() => loadServerConfig({})).toThrow(/ENGINE_SHARED_SECRET/);
  });

  it("rejects a malformed engine URL", () => {
    expect(() => loadServerConfig({ ENGINE_URL: "not a url", ENGINE_SHARED_SECRET: "x" })).toThrow(/ENGINE_URL/);
  });
});
