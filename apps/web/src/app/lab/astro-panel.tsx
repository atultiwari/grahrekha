"use client";

import type { AstroChartV1, AstroReadingV1, PlaceV1, PlacesResponseV1 } from "@grahrekha/contracts";
import { useEffect, useState } from "react";
import { RuleCard } from "./rule-card";

type Confidence = "exact" | "approximate" | "unknown";
type ChartResponse = AstroReadingV1 | { error: string };

const SEARCH_DELAY_MS = 250;

interface SearchState {
  query: string;
  places: PlaceV1[];
  attribution: string;
  error: string | null;
}

const EMPTY_SEARCH: SearchState = { query: "", places: [], attribution: "", error: null };

/** Debounced place lookup. Results are tied to the query that produced them, so stale ones never show. */
function usePlaceSearch(query: string, selected: PlaceV1 | null) {
  const [state, setState] = useState<SearchState>(EMPTY_SEARCH);
  const q = query.trim();
  const active = q.length >= 2 && !selected;

  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/lab/places?q=${encodeURIComponent(q)}`, { signal: controller.signal });
        const body = (await response.json()) as PlacesResponseV1 | { error: string };
        setState((previous) =>
          "error" in body
            ? { ...previous, query: q, places: [], error: body.error }
            : { query: q, places: body.places, attribution: body.attribution, error: null },
        );
      } catch (cause) {
        if ((cause as Error).name !== "AbortError") {
          setState((previous) => ({ ...previous, query: q, places: [], error: "Could not reach the server." }));
        }
      }
    }, SEARCH_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [q, active]);

  const current = active && state.query === q;
  return {
    places: current ? state.places : [],
    error: current ? state.error : null,
    attribution: state.attribution,
  };
}

export function AstroPanel() {
  const [query, setQuery] = useState("");
  const [place, setPlace] = useState<PlaceV1 | null>(null);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [confidence, setConfidence] = useState<Confidence>("exact");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ChartResponse | null>(null);
  const search = usePlaceSearch(query, place);

  function pick(next: PlaceV1) {
    setPlace(next);
    setQuery(label(next));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!place) return;
    setBusy(true);
    setResult(null);
    const timeKnown = confidence !== "unknown";
    try {
      const response = await fetch("/api/lab/astro", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          birth_date: date,
          birth_time: timeKnown ? time : "",
          time_confidence: confidence,
          latitude: place.latitude,
          longitude: place.longitude,
          timezone: place.timezone,
        }),
      });
      setResult((await response.json()) as ChartResponse);
    } catch {
      setResult({ error: "Could not reach the server." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="astro-heading" className="space-y-4">
      <h2 id="astro-heading" className="text-xl font-semibold">
        Birth chart (sidereal, Vimshottari)
      </h2>
      <form onSubmit={submit} className="flex flex-wrap items-end gap-4 rounded-lg border p-4">
        <div className="relative flex flex-col gap-1 text-sm">
          <label htmlFor="birthplace">Birthplace</label>
          <input
            id="birthplace"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPlace(null);
            }}
            placeholder="e.g. Varanasi, Banaras, वाराणसी"
            autoComplete="off"
            role="combobox"
            aria-expanded={search.places.length > 0}
            aria-controls="birthplace-options"
            className="w-72 rounded border px-2 py-1"
          />
          {search.places.length > 0 && (
            <ul
              id="birthplace-options"
              role="listbox"
              className="absolute top-full z-10 mt-1 w-72 rounded border bg-white shadow dark:bg-zinc-900"
            >
              {search.places.map((p) => (
                <li key={p.geoname_id} role="option" aria-selected={false}>
                  <button
                    type="button"
                    onClick={() => pick(p)}
                    className="w-full px-2 py-1 text-left hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  >
                    {label(p)} <span className="text-xs text-zinc-500">{p.timezone}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {search.error && <span className="text-xs text-red-700">{search.error}</span>}
        </div>
        <label className="flex flex-col gap-1 text-sm">
          Date of birth
          <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} className="rounded border px-2 py-1" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Time is
          <select
            value={confidence}
            onChange={(e) => setConfidence(e.target.value as Confidence)}
            className="rounded border px-2 py-1"
          >
            <option value="exact">Exact</option>
            <option value="approximate">Approximate</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        {confidence !== "unknown" && (
          <label className="flex flex-col gap-1 text-sm">
            Time of birth (local)
            <input type="time" required value={time} onChange={(e) => setTime(e.target.value)} className="rounded border px-2 py-1" />
          </label>
        )}
        <button
          type="submit"
          disabled={!place || !date || busy}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {busy ? "Calculating…" : "Calculate"}
        </button>
      </form>
      {search.attribution && <p className="text-xs text-zinc-500">Places: {search.attribution}</p>}

      {result && "error" in result && (
        <p role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          {result.error}
        </p>
      )}
      {result && "chart" in result && (
        <>
          <Chart chart={result.chart} />
          {result.features.lagna_margin_deg !== null && result.features.lagna_margin_deg < 2 && (
            <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
              The lagna is only {result.features.lagna_margin_deg.toFixed(2)}° from the next sign. A birth time a few
              minutes off would change every house, so house and lordship rules are withheld.
            </p>
          )}
          <div className="space-y-2 text-sm">
            <h3 className="font-semibold">
              Reading (unreviewed rules, rule base {result.rules.rulebase_version})
            </h3>
            {result.rules.fired.length === 0 && (
              <p>No rules matched. House and dasha rules need an exact birth time.</p>
            )}
            <ul className="space-y-3">
              {result.rules.fired.map((rule) => (
                <RuleCard key={rule.id} rule={rule} />
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  );
}

function label(p: PlaceV1): string {
  return [p.name, p.region, p.country].filter(Boolean).join(", ");
}

function Chart({ chart }: { chart: AstroChartV1 }) {
  return (
    <div className="grid gap-6 text-sm md:grid-cols-2">
      <div className="space-y-2">
        <p>
          Lagna: <strong>{chart.lagna_sign ? `${chart.lagna_sign} ${chart.lagna_degree?.toFixed(2)}°` : "withheld (birth time unknown)"}</strong>
          {chart.navamsa_lagna_sign && <> · D9 lagna {chart.navamsa_lagna_sign}</>}
        </p>
        <p>
          Moon nakshatra: <strong>{chart.moon_nakshatra}</strong>
          {chart.moon_nakshatra_uncertain && " (may differ: the Moon changes nakshatra on this day)"}
        </p>
        <p>
          Current dasha: <strong>{chart.current_mahadasha ?? "–"}</strong> / {chart.current_antardasha ?? "–"}
        </p>
        <p className="text-xs text-zinc-500">
          {chart.provider}, {chart.ayanamsa} ayanamsa, {chart.timezone} (UTC{chart.utc_offset_hours >= 0 ? "+" : ""}
          {chart.utc_offset_hours})
        </p>
        {chart.time_confidence !== "exact" && (
          <p className="text-xs text-amber-700 dark:text-amber-300">
            Dasha dates follow the Moon, which moves about 13° a day: without an exact birth time they can be off by
            months or, if the time is unknown, years.
          </p>
        )}
        <ol className="text-xs">
          {chart.mahadashas.map((d) => (
            <li key={`${d.lord}-${d.start}`} className={d.lord === chart.current_mahadasha ? "font-semibold" : ""}>
              {d.lord}: {d.start} → {d.end}
            </li>
          ))}
        </ol>
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left">
            <th>Graha</th>
            <th>Sign</th>
            <th>Degree</th>
            <th>Nakshatra</th>
            <th>House</th>
            <th>D9</th>
          </tr>
        </thead>
        <tbody>
          {chart.planets.map((p) => (
            <tr key={p.planet} className="border-t">
              <td>
                {p.planet}
                {p.retrograde && p.planet !== "Rahu" && p.planet !== "Ketu" ? " (R)" : ""}
              </td>
              <td>{p.sign}</td>
              <td>{p.degree_in_sign.toFixed(2)}°</td>
              <td>
                {p.nakshatra} {p.pada}
              </td>
              <td>{p.house ?? "–"}</td>
              <td>{p.navamsa_sign}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
