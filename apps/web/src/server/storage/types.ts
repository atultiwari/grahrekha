/** Storage areas (docs/ARCHITECTURE.md §9). Raw captures live in captures-tmp for at most 24 h. */
export const STORAGE_AREAS = ["captures-tmp", "captures-retained", "training"] as const;
export type StorageArea = (typeof STORAGE_AREAS)[number];

/**
 * Blob storage behind an interface so the POC's local filesystem can later be
 * swapped for S3-compatible storage without touching callers (D-012).
 */
export interface StorageAdapter {
  put(area: StorageArea, key: string, data: Uint8Array): Promise<void>;
  get(area: StorageArea, key: string): Promise<Uint8Array | null>;
  /** Returns true if something was deleted. */
  delete(area: StorageArea, key: string): Promise<boolean>;
  /** Keys whose last modification is strictly before `cutoff`. */
  listOlderThan(area: StorageArea, cutoff: Date): Promise<string[]>;
}
