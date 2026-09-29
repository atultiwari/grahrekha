import { describe, expect, it, vi } from "vitest";
import { createEngineClient } from "../src/server/engine-client";
import { chartFixture, placesFixture, readingFixture } from "./fixtures";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

const BIRTH = {
  birth_date: "1996-07-04",
  birth_time: "09:10:00",
  time_confidence: "exact",
  latitude: 18.404,
  longitude: 75.195,
  timezone: null,
} as const;

describe("engine client: astrology", () => {
  it("searches places with an encoded query and limit", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json(placesFixture()));
    const engine = createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn });

    const result = await engine.searchPlaces("São Paulo & co", 5);

    expect(result.places[0]?.name).toBe("Varanasi");
    const [url] = fetchFn.mock.calls[0] as [string];
    expect(url).toBe("http://e/v1/places?q=S%C3%A3o+Paulo+%26+co&limit=5");
  });

  it("posts birth data with an explicit reference date and validates the chart", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json(chartFixture()));
    const engine = createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn });

    const chart = await engine.astroChart(BIRTH, "2026-09-30");

    expect(chart.current_mahadasha).toBe("Jupiter");
    const [url, init] = fetchFn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://e/v1/astro/chart");
    expect(JSON.parse(init.body as string)).toEqual({ birth: BIRTH, reference_date: "2026-09-30" });
  });

  it("rejects a chart that breaks the contract", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json({ ...chartFixture(), lagna_sign: "Ophiuchus" }));
    const engine = createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn });
    await expect(engine.astroChart(BIRTH, "2026-09-30")).rejects.toMatchObject({ status: 502 });
  });

  it("requests a reading with the lab flag and validates it", async () => {
    const fetchFn = vi.fn().mockResolvedValue(json(readingFixture()));
    const engine = createEngineClient({ baseUrl: "http://e", secret: "s", fetchFn });

    const reading = await engine.astroReading(BIRTH, "2026-09-30", true);

    expect(reading.rules.fired[0]?.id).toBe("astro.jc.mahadasha_lord_rules_trikona");
    const [url, init] = fetchFn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://e/v1/astro/reading");
    expect(JSON.parse(init.body as string)).toEqual({ birth: BIRTH, reference_date: "2026-09-30", include_unreviewed: true });
  });
});
