import { mkdir, readdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { STORAGE_AREAS, type StorageAdapter, type StorageArea } from "./types";

// Flat, conservative keys: no separators, no leading dot, bounded length.
// This is what makes path traversal impossible, rather than path normalisation.
const KEY_PATTERN = /^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,63}$/;

export class InvalidStorageKeyError extends Error {
  constructor(key: string) {
    super(`invalid storage key: ${JSON.stringify(key)}`);
    this.name = "InvalidStorageKeyError";
  }
}

function assertArea(area: string): asserts area is StorageArea {
  if (!(STORAGE_AREAS as readonly string[]).includes(area)) throw new Error(`unknown storage area: ${area}`);
}

function assertKey(key: string): void {
  if (!KEY_PATTERN.test(key) || key.includes("..")) throw new InvalidStorageKeyError(key);
}

const isNotFound = (error: unknown) => (error as NodeJS.ErrnoException).code === "ENOENT";

/** Local filesystem storage rooted at `root` (e.g. <repo>/var/uploads). */
export function createLocalStorage(root: string): StorageAdapter {
  const pathFor = (area: StorageArea, key: string) => {
    assertArea(area);
    assertKey(key);
    return join(root, area, key);
  };

  return {
    async put(area, key, data) {
      const target = pathFor(area, key);
      await mkdir(join(root, area), { recursive: true });
      // Write then rename so readers never see a half-written file.
      const temp = `${target}.${process.pid}.${Date.now()}.partial`;
      await writeFile(temp, data, { mode: 0o600 });
      await rename(temp, target);
    },
    async get(area, key) {
      try {
        return new Uint8Array(await readFile(pathFor(area, key)));
      } catch (error) {
        if (isNotFound(error)) return null;
        throw error;
      }
    },
    async delete(area, key) {
      const target = pathFor(area, key);
      try {
        await stat(target);
      } catch (error) {
        if (isNotFound(error)) return false;
        throw error;
      }
      await rm(target);
      return true;
    },
    async listOlderThan(area, cutoff) {
      assertArea(area);
      let names: string[];
      try {
        names = await readdir(join(root, area));
      } catch (error) {
        if (isNotFound(error)) return [];
        throw error;
      }
      const old: string[] = [];
      for (const name of names.filter((n) => KEY_PATTERN.test(n) && !n.endsWith(".partial")).sort()) {
        const info = await stat(join(root, area, name));
        if (info.mtime < cutoff) old.push(name);
      }
      return old;
    },
  };
}
