import { describe, expect, it, vi } from "vitest";
import { createEngineClient, EngineError } from "../src/server/engine-client";

const ok = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

describe("engine client", () => {
  it("returns a validated health response", async () => {
    const fetchFn = vi.fn().mockResolvedValue(ok({ status: "ok", version: "0.1.0" }));
    const engine = createEngineClient({ baseUrl: "http://engine:8000", secret: "s", fetchFn });

    await expect(engine.health()).resolves.toEqual({ status: "ok", version: "0.1.0" });
    expect(fetchFn).toHaveBeenCalledWith(
      "http://engine:8000/healthz",
      expect.objectContaining({ headers: expect.objectContaining({ "X-Engine-Secret": "s" }) }),
    );
  });

  it("rejects a response that breaks the contract", async () => {
    const fetchFn = vi.fn().mockResolvedValue(ok({ status: "ok" }));
    const engine = createEngineClient({ baseUrl: "http://engine", secret: "s", fetchFn });
    await expect(engine.health()).rejects.toBeInstanceOf(EngineError);
  });

  it("maps non-2xx responses to EngineError with the status", async () => {
    const fetchFn = vi.fn().mockResolvedValue(ok({ detail: "nope" }, 401));
    const engine = createEngineClient({ baseUrl: "http://engine", secret: "s", fetchFn });
    await expect(engine.health()).rejects.toMatchObject({ status: 401 });
  });

  it("maps network failures to EngineError", async () => {
    const fetchFn = vi.fn().mockRejectedValue(new TypeError("fetch failed"));
    const engine = createEngineClient({ baseUrl: "http://engine", secret: "s", fetchFn });
    await expect(engine.health()).rejects.toMatchObject({ status: 503 });
  });

  it("strips a trailing slash from the base URL", async () => {
    const fetchFn = vi.fn().mockResolvedValue(ok({ status: "ok", version: "1" }));
    await createEngineClient({ baseUrl: "http://engine/", secret: "s", fetchFn }).health();
    expect(fetchFn.mock.calls[0]?.[0]).toBe("http://engine/healthz");
  });

  it("maps a non-JSON 200 body to a 502 EngineError", async () => {
    const fetchFn = vi.fn().mockResolvedValue(new Response("<html>proxy error</html>", { status: 200 }));
    const engine = createEngineClient({ baseUrl: "http://engine", secret: "s", fetchFn });
    await expect(engine.health()).rejects.toMatchObject({ name: "EngineError", status: 502 });
  });
});
