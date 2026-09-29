"use client";

import type { FiredRuleV1, PalmAnalysisV1, RulesResponseV1 } from "@grahrekha/contracts";
import { useState } from "react";
import { AstroPanel } from "./astro-panel";

type LabResponse = { analysis: PalmAnalysisV1; rules: RulesResponseV1 | null } | { error: string };

const LINE_COLOURS: Record<string, string> = {
  heart: "#ef4444",
  head: "#3b82f6",
  life: "#22c55e",
  fate: "#f59e0b",
};

export function LabClient() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [hand, setHand] = useState<"" | "left" | "right">("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<LabResponse | null>(null);

  function choose(next: File | null) {
    if (preview) URL.revokeObjectURL(preview);
    setFile(next);
    setPreview(next ? URL.createObjectURL(next) : null);
    setResult(null);
  }

  async function analyse(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setResult(null);
    const form = new FormData();
    form.set("file", file);
    if (hand) form.set("declared_hand", hand);
    try {
      const response = await fetch("/api/lab/palm", { method: "POST", body: form });
      setResult((await response.json()) as LabResponse);
    } catch {
      setResult({ error: "Could not reach the server." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">GrahRekha lab</h1>
        <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
          Research prototype. Rules shown here are <strong>unreviewed</strong> extracts from public-domain
          books, and some are known to be affected by measurement limits. For entertainment and self-reflection
          only; no health, lifespan or medical claims.
        </p>
      </header>

      <form onSubmit={analyse} className="flex flex-wrap items-end gap-4 rounded-lg border p-4">
        <label className="flex flex-col gap-1 text-sm">
          Palm photo
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => choose(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Which hand?
          <select value={hand} onChange={(e) => setHand(e.target.value as typeof hand)} className="rounded border px-2 py-1">
            <option value="">Not sure</option>
            <option value="left">Left</option>
            <option value="right">Right</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {busy ? "Analysing…" : "Analyse"}
        </button>
      </form>

      {result && "error" in result && (
        <p role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          {result.error}
        </p>
      )}

      {result && "analysis" in result && preview && (
        <Results analysis={result.analysis} rules={result.rules} preview={preview} />
      )}

      <hr />
      <AstroPanel />
    </main>
  );
}

function Results({ analysis, rules, preview }: { analysis: PalmAnalysisV1; rules: RulesResponseV1 | null; preview: string }) {
  const { gate, overlay, features } = analysis;
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section aria-label="Photo with detected lines" className="space-y-2">
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element -- local object URL */}
          <img src={preview} alt="Your palm photo" className="w-full rounded-lg" />
          {overlay && (
            <svg viewBox={`0 0 ${overlay.width} ${overlay.height}`} className="absolute inset-0 h-full w-full">
              {Object.entries(overlay.lines).map(([name, segments]) =>
                (segments ?? []).map((segment, i) => (
                  <polyline
                    key={`${name}-${i}`}
                    points={segment.map(([x, y]) => `${x},${y}`).join(" ")}
                    fill="none"
                    stroke={LINE_COLOURS[name] ?? "#fff"}
                    strokeWidth={Math.max(3, overlay.width / 250)}
                    strokeLinecap="round"
                    data-line={name}
                  />
                )),
              )}
              {overlay.landmarks.map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r={Math.max(3, overlay.width / 300)} fill="white" stroke="black" />
              ))}
            </svg>
          )}
        </div>
        <p className="flex flex-wrap gap-3 text-xs">
          {Object.entries(LINE_COLOURS).map(([name, colour]) => (
            <span key={name} className="flex items-center gap-1">
              <span className="inline-block h-2 w-4 rounded" style={{ background: colour }} /> {name}
            </span>
          ))}
        </p>
      </section>

      <section className="space-y-4 text-sm">
        <div>
          <h2 className="mb-1 font-semibold">Quality gate: {gate.passed ? "passed" : "rejected"}</h2>
          <ul className="list-disc pl-5">
            {gate.reasons.map((r) => (
              <li key={r.code}>
                <code>{r.code}</code>: {r.message}
              </li>
            ))}
            {gate.warnings.map((w) => (
              <li key={w.code} className="text-amber-700">
                <code>{w.code}</code>: {w.message}
              </li>
            ))}
          </ul>
        </div>

        {features && (
          <div>
            <h2 className="mb-1 font-semibold">Measured features</h2>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left">
                  <th>Line</th>
                  <th>Length</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Breaks</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(features.lines).map((line) => (
                  <tr key={line.name} className="border-t">
                    <td>{line.name}</td>
                    <td>{line.present ? line.length.toFixed(2) : "not found"}</td>
                    <td>{zone(line.start_zone, line.start_zone_certain)}</td>
                    <td>{zone(line.end_zone, line.end_zone_certain)}</td>
                    <td>{line.present ? line.breaks : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-zinc-500">
              Hand: palm {features.hand_geometry.palm_shape}, fingers {features.hand_geometry.finger_length}, element{" "}
              {features.hand_geometry.element} (experimental). Lengths in palm lengths.
            </p>
          </div>
        )}

        {rules && (
          <div>
            <h2 className="mb-1 font-semibold">Reading (unreviewed rules, rule base {rules.rulebase_version})</h2>
            {rules.fired.length === 0 && <p>No rules matched these measurements.</p>}
            <ul className="space-y-3">
              {rules.fired.map((rule) => (
                <RuleCard key={rule.id} rule={rule} />
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}

function zone(name: string | null | undefined, certain: boolean | undefined) {
  if (!name) return "";
  return certain ? name : `${name} (uncertain)`;
}

function RuleCard({ rule }: { rule: FiredRuleV1 }) {
  return (
    <li className="rounded-md border p-3">
      <p>{rule.statement.en}</p>
      <details className="mt-2 text-xs text-zinc-600 dark:text-zinc-400">
        <summary className="cursor-pointer">
          Why? <code>{rule.id}</code> · {rule.status}
        </summary>
        <p className="mt-1">
          {rule.source.work}, {rule.source.locator}
        </p>
        {rule.source.quote && <blockquote className="mt-1 border-l-2 pl-2 italic">{rule.source.quote}</blockquote>}
        {rule.mapping_note && <p className="mt-1">Mapping: {rule.mapping_note}</p>}
      </details>
      {rule.validity_blocker && (
        <p className="mt-2 rounded bg-red-50 p-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200">
          Known measurement issue: {rule.validity_blocker}
        </p>
      )}
    </li>
  );
}
