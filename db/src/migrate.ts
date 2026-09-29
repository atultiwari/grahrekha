import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { migrate as drizzleMigrate } from "drizzle-orm/better-sqlite3/migrator";
import type { Database } from "./client";

export const MIGRATIONS_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "migrations");

/** Applies all pending SQL migrations in order. Idempotent. */
export function migrate(db: Database): void {
  drizzleMigrate(db, { migrationsFolder: MIGRATIONS_DIR });
}
