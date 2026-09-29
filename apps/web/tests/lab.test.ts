import { describe, expect, it, vi } from "vitest";
import { handleLabPalm, isLabEnabled } from "../src/server/lab";
import { analysisFixture } from "./fixtures";

const upload = (bytes = 10, type = "image/jpeg") => {
  const form = new FormData();
  form.set("file", new File([new Uint8Array(bytes)], "palm.jpg", { type }));
  form.set("declared_hand", "right");
  return form;
};

const engine = () => ({
  analyzePalm: vi.fn().mockResolvedValue(analysisFixture()),
  evaluateRules: vi.fn().mockResolvedValue({ rulebase_version: "abc", fired: [] }),
});

describe("lab mode", () => {
  it("is on in development and off in production unless LAB_ENABLED=true", () => {
    expect(isLabEnabled({ NODE_ENV: "development" })).toBe(true);
    expect(isLabEnabled({ NODE_ENV: "production" })).toBe(false);
    expect(isLabEnabled({ NODE_ENV: "production", LAB_ENABLED: "true" })).toBe(true);
  });
});

describe("lab palm handler", () => {
  it("analyses the upload and fires unreviewed rules for the lab", async () => {
    const e = engine();
    const result = await handleLabPalm(upload(), e);
    expect(result.status).toBe(200);
    expect(e.analyzePalm).toHaveBeenCalledWith(expect.any(File), "palm.jpg", "right");
    expect(e.evaluateRules).toHaveBeenCalledWith(expect.anything(), true);
  });

  it("does not evaluate rules when the gate rejected the photo", async () => {
    const e = engine();
    e.analyzePalm.mockResolvedValue({ ...analysisFixture(), features: null, overlay: null });
    const result = await handleLabPalm(upload(), e);
    expect(result.status).toBe(200);
    expect(e.evaluateRules).not.toHaveBeenCalled();
    expect(result.body).toMatchObject({ rules: null });
  });

  it.each([
    ["missing file", new FormData(), 400],
    ["non-image type", upload(10, "application/pdf"), 415],
    ["oversized file", upload(20 * 1024 * 1024 + 1), 413],
  ])("rejects %s", async (_label, form, status) => {
    expect((await handleLabPalm(form, engine())).status).toBe(status);
  });

  it("rejects an invalid declared hand", async () => {
    const form = upload();
    form.set("declared_hand", "middle");
    expect((await handleLabPalm(form, engine())).status).toBe(400);
  });
});
