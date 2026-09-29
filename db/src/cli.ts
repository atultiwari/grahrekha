/** db CLI: `migrate` | `reset` | `snapshot`. The database lives at <repo>/var/app.db unless DATABASE_PATH is set. */
import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { openDatabase } from "./client";
import { migrate } from "./migrate";
import { renderSchemaSql } from "./snapshot";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const dbPath = process.env.DATABASE_PATH ?? join(repoRoot, "var", "app.db");
const snapshotPath = join(repoRoot, "db", "schema.sql");

function run(command: string | undefined): void {
  switch (command) {
    case "migrate": {
      mkdirSync(dirname(dbPath), { recursive: true });
      migrate(openDatabase(dbPath));
      console.info(`migrated ${dbPath}`);
      return;
    }
    case "reset": {
      for (const suffix of ["", "-wal", "-shm"]) {
        if (existsSync(dbPath + suffix)) rmSync(dbPath + suffix);
      }
      run("migrate");
      return;
    }
    case "snapshot": {
      const db = openDatabase(":memory:");
      migrate(db);
      writeFileSync(snapshotPath, renderSchemaSql(db));
      console.info(`wrote ${snapshotPath}`);
      return;
    }
    default:
      console.error("usage: cli.ts <migrate|reset|snapshot>");
      process.exitCode = 2;
  }
}

run(process.argv[2]);
