/**
 * Database schema (SQLite, portable to Postgres — see docs/DECISIONS.md D-012).
 * Conventions: ULID text ids, ISO-8601 UTC timestamps as TEXT, JSON as TEXT.
 */
import { sql } from "drizzle-orm";
import { check, index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const MARKETS = ["in", "global"] as const;
export type Market = (typeof MARKETS)[number];

export const CONSENT_TYPES = [
  "processing",
  "biometric",
  "retain_images",
  "training_data",
  "research",
] as const;
export type ConsentType = (typeof CONSENT_TYPES)[number];

const nowIso = sql`(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))`;

export const profiles = sqliteTable(
  "profiles",
  {
    id: text("id").primaryKey(),
    market: text("market", { enum: MARKETS }).notNull(),
    locale: text("locale").notNull(),
    birthYear: integer("birth_year"),
    isAdult: integer("is_adult", { mode: "boolean" }).notNull().default(false),
    createdAt: text("created_at").notNull().default(nowIso),
  },
  (t) => [check("profiles_market_check", sql`${t.market} IN ('in', 'global')`)],
);

export const consents = sqliteTable(
  "consents",
  {
    id: text("id").primaryKey(),
    profileId: text("profile_id")
      .notNull()
      .references(() => profiles.id, { onDelete: "cascade" }),
    type: text("type", { enum: CONSENT_TYPES }).notNull(),
    // "grant" or "withdraw"; the latest row per (profile, type) wins. Append-only.
    action: text("action", { enum: ["grant", "withdraw"] }).notNull(),
    version: text("version"),
    createdAt: text("created_at").notNull().default(nowIso),
  },
  (t) => [
    index("consents_profile_type_idx").on(t.profileId, t.type),
    check(
      "consents_type_check",
      sql`${t.type} IN ('processing', 'biometric', 'retain_images', 'training_data', 'research')`,
    ),
  ],
);

export type Profile = typeof profiles.$inferSelect;
export type Consent = typeof consents.$inferSelect;
