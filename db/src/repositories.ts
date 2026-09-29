/**
 * Repository layer. SQLite has no row-level security, so every read/write that
 * belongs to a user is scoped by profileId here (docs/ARCHITECTURE.md §9).
 */
import { and, desc, eq } from "drizzle-orm";
import { monotonicFactory } from "ulid";
import type { Database } from "./client";
import {
  CONSENT_TYPES,
  MARKETS,
  consents,
  profiles,
  type Consent,
  type ConsentType,
  type Market,
  type Profile,
} from "./schema";

// Monotonic: ids created within the same millisecond still sort in creation order,
// which isActive() relies on to find the latest consent action.
const ulid = monotonicFactory();

export interface NewProfile {
  market: Market;
  locale: string;
  birthYear?: number;
  isAdult?: boolean;
}

export function createProfileRepository(db: Database) {
  return {
    create(input: NewProfile): Profile {
      if (!MARKETS.includes(input.market)) throw new Error(`unsupported market: ${input.market}`);
      return db
        .insert(profiles)
        .values({ id: ulid(), ...input })
        .returning()
        .get();
    },
    findById(id: string): Profile | null {
      return db.select().from(profiles).where(eq(profiles.id, id)).get() ?? null;
    },
  };
}

export interface ConsentGrant {
  type: ConsentType;
  version: string;
}

export function createConsentRepository(db: Database) {
  const append = (profileId: string, type: ConsentType, action: "grant" | "withdraw", version?: string) => {
    if (!CONSENT_TYPES.includes(type)) throw new Error(`unsupported consent type: ${type}`);
    return db
      .insert(consents)
      .values({ id: ulid(), profileId, type, action, version })
      .returning()
      .get();
  };

  return {
    grant(profileId: string, input: ConsentGrant): Consent {
      return append(profileId, input.type, "grant", input.version);
    },
    withdraw(profileId: string, type: ConsentType): Consent {
      return append(profileId, type, "withdraw");
    },
    listForProfile(profileId: string): Consent[] {
      return db.select().from(consents).where(eq(consents.profileId, profileId)).all();
    },
    isActive(profileId: string, type: ConsentType): boolean {
      const latest = db
        .select()
        .from(consents)
        .where(and(eq(consents.profileId, profileId), eq(consents.type, type)))
        // ULIDs sort by creation time, so the last id is the latest action.
        .orderBy(desc(consents.id))
        .get();
      return latest?.action === "grant";
    },
  };
}
