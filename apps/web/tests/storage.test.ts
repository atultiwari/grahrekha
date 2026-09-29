import { mkdtempSync, rmSync, utimesSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createLocalStorage, InvalidStorageKeyError } from "../src/server/storage/local";
import type { StorageAdapter } from "../src/server/storage/types";

let root: string;
let storage: StorageAdapter;
const bytes = new Uint8Array([1, 2, 3]);

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "grahrekha-storage-"));
  storage = createLocalStorage(root);
});
afterEach(() => rmSync(root, { recursive: true, force: true }));

describe("local storage adapter", () => {
  it("round-trips bytes within an area", async () => {
    await storage.put("captures-tmp", "cap_01.jpg", bytes);
    expect(await storage.get("captures-tmp", "cap_01.jpg")).toEqual(bytes);
    expect(await storage.get("captures-retained", "cap_01.jpg")).toBeNull();
  });

  it("returns null for a missing key and reports deletions", async () => {
    expect(await storage.get("captures-tmp", "missing.jpg")).toBeNull();
    await storage.put("captures-tmp", "a.jpg", bytes);
    expect(await storage.delete("captures-tmp", "a.jpg")).toBe(true);
    expect(await storage.delete("captures-tmp", "a.jpg")).toBe(false);
  });

  it.each(["../escape.jpg", "a/b.jpg", "..", "", ".hidden", "a b.jpg", "x".repeat(100)])(
    "rejects unsafe key %j (no path traversal)",
    async (key) => {
      await expect(storage.put("captures-tmp", key, bytes)).rejects.toBeInstanceOf(InvalidStorageKeyError);
    },
  );

  it("rejects an unknown area", async () => {
    // @ts-expect-error area is a closed union
    await expect(storage.put("../../etc", "a.jpg", bytes)).rejects.toThrow();
  });

  it("lists keys last modified before a cutoff (for the 24 h deletion job)", async () => {
    await storage.put("captures-tmp", "old.jpg", bytes);
    await storage.put("captures-tmp", "new.jpg", bytes);
    const twoDaysAgo = new Date(Date.now() - 48 * 3600 * 1000);
    utimesSync(join(root, "captures-tmp", "old.jpg"), twoDaysAgo, twoDaysAgo);

    const cutoff = new Date(Date.now() - 24 * 3600 * 1000);
    expect(await storage.listOlderThan("captures-tmp", cutoff)).toEqual(["old.jpg"]);
  });

  it("lists nothing for an area that has never been written", async () => {
    expect(await storage.listOlderThan("training", new Date())).toEqual([]);
  });
});
