import { describe, expect, it, vi } from "vitest";
import { createEngineClient } from "../src/server/engine-client";
import { analysisFixture, featuresFixture } from "./fixtures";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

describe("engine client: palm + rules", () => {
  it("posts the photo as multipart with the declared hand and validates the analysis", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json(analysisFixture()));
    const engine = createEngineClient({ baseUrl: "http://engine", secret: "s", fetchFn });

    const result = await engine.analyzePalm(new Blob(["img"], { type: "image/jpeg" }), "palm.jpg", "left");

    expect(result.gate.passed).toBe(true);
    const [url, init] = fetchFn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://engine/v1/palm/analyze");
    expect(init.method).toBe("POST");
    const form = init.body as FormData;
    expect((form.get("file") as File).name).toBe("palm.jpg");
    expect(form.get("declared_hand")).toBe("left");
  });

  it("omits declared_hand when unknown", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json(analysisFixture()));
    await createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn }).analyzePalm(new Blob(["x"]), "p.jpg", null);
    expect((fetchFn.mock.calls[0]?.[1] as RequestInit & { body: FormData }).body.has("declared_hand")).toBe(false);
  });

  it("surfaces the engine's user-safe message for rejected uploads", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json({ detail: "file is not a readable image" }, 400));
    const engine = createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn });
    await expect(engine.analyzePalm(new Blob(["x"]), "p.jpg", null)).rejects.toMatchObject({
      status: 400,
      userMessage: "file is not a readable image",
    });
  });

  it("evaluates rules with the lab flag and validates the response", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json({ rulebase_version: "abcdef123456", fired: [] }));
    const engine = createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn });

    const result = await engine.evaluateRules(featuresFixture(), true);

    expect(result.rulebase_version).toBe("abcdef123456");
    const init = fetchFn.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(init.body as string)).toMatchObject({ include_unreviewed: true });
    expect((init.headers as Record<string, string>)["content-type"]).toBe("application/json");
  });
});
