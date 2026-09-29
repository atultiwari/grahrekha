import BetterSqlite3 from "better-sqlite3";
import { drizzle, type BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

export type Database = BetterSQLite3Database<typeof schema> & { $client: BetterSqlite3.Database };

/** Opens a SQLite database (file path or ":memory:") with safe defaults. */
export function openDatabase(path: string): Database {
  const sqlite = new BetterSqlite3(path);
  sqlite.pragma("journal_mode = WAL");
  sqlite.pragma("foreign_keys = ON");
  return drizzle(sqlite, { schema });
}
