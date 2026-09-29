import { describe, expect, it, vi } from "vitest";
import { EngineError } from "../src/server/engine-client";
import { handleLabChart, handleLabPlaces } from "../src/server/lab-astro";
import { chartFixture, placesFixture } from "./fixtures";

const engine = () => ({
  searchPlaces: vi.fn().mockResolvedValue(placesFixture()),
  astroChart: vi.fn().mockResolvedValue(chartFixture()),
});

const BIRTH = { birth_date: "1996-07-04", birth_time: "09:10", time_confidence: "exact", latitude: 25.3, longitude: 83.0 };
const TODAY = new Date("2026-09-30T18:00:00Z");

describe("lab place search", () => {
  it("trims the query and returns places", async () => {
    const e = engine();
    const result = await handleLabPlaces("  banaras ", e);
    expect(result.status).toBe(200);
    expect(e.searchPlaces).toHaveBeenCalledWith("banaras", 8);
  });

  it.each([[null], [""], ["   "], ["x".repeat(101)]])("rejects query %j without calling the engine", async (q) => {
    const e = engine();
    expect((await handleLabPlaces(q, e)).status).toBe(400);
    expect(e.searchPlaces).not.toHaveBeenCalled();
  });

  it("maps engine outages to a friendly 503", async () => {
    const e = engine();
    e.searchPlaces.mockRejectedValue(new EngineError("down", 503));
    const result = await handleLabPlaces("delhi", e);
    expect(result).toMatchObject({ status: 503, body: { error: expect.stringContaining("unavailable") } });
  });
});

describe("lab chart", () => {
  it("normalises HH:MM to HH:MM:SS and uses today's date as the reference", async () => {
    const e = engine();
    const result = await handleLabChart(BIRTH, e, TODAY);
    expect(result.status).toBe(200);
    expect(e.astroChart).toHaveBeenCalledWith(
      expect.objectContaining({ birth_time: "09:10:00", time_confidence: "exact" }),
      "2026-09-30",
    );
  });

  it("sends an unknown time as null with confidence 'unknown'", async () => {
    const e = engine();
    await handleLabChart({ ...BIRTH, birth_time: "", time_confidence: "unknown" }, e, TODAY);
    expect(e.astroChart).toHaveBeenCalledWith(
      expect.objectContaining({ birth_time: null, time_confidence: "unknown" }),
      "2026-09-30",
    );
  });

  it.each([
    ["missing date", { ...BIRTH, birth_date: "" }],
    ["bad latitude", { ...BIRTH, latitude: 91 }],
    ["time without confidence", { ...BIRTH, time_confidence: "unknown" }],
    ["confidence without time", { ...BIRTH, birth_time: "" }],
    ["not an object", "hello"],
  ])("rejects %s with 400", async (_label, body) => {
    const e = engine();
    const result = await handleLabChart(body, e, TODAY);
    expect(result.status).toBe(400);
    expect(e.astroChart).not.toHaveBeenCalled();
  });
});
