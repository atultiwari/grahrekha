import { readFileSync } from "node:fs";
import { join } from "node:path";
import BetterSqlite3 from "better-sqlite3";
import { describe, expect, it } from "vitest";
import { openDatabase } from "../src/client";
import { migrate } from "../src/migrate";
import { renderSchemaSql } from "../src/snapshot";

const committed = readFileSync(join(__dirname, "..", "schema.sql"), "utf8");

describe("schema.sql snapshot", () => {
  it("matches the migrations (run `pnpm db:snapshot` after adding a migration)", () => {
    const db = openDatabase(":memory:");
    migrate(db);
    expect(renderSchemaSql(db)).toBe(committed);
  });

  it("can be applied directly for one-click setup", () => {
    const raw = new BetterSqlite3(":memory:");
    raw.exec(committed);
    const tables = raw
      .prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
      .all() as { name: string }[];
    expect(tables.map((t) => t.name)).toEqual(["consents", "profiles"]);
  });
});
