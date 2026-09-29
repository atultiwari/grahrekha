import { beforeEach, describe, expect, it } from "vitest";
import { openDatabase, type Database } from "../src/client";
import { migrate } from "../src/migrate";
import { createConsentRepository, createProfileRepository } from "../src/repositories";

let db: Database;

beforeEach(() => {
  db = openDatabase(":memory:");
  migrate(db);
});

describe("profile repository", () => {
  it("creates a profile with a ULID id and defaults", () => {
    const profiles = createProfileRepository(db);
    const created = profiles.create({ market: "in", locale: "hi" });

    expect(created.id).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(created.market).toBe("in");
    expect(created.locale).toBe("hi");
    expect(created.isAdult).toBe(false);
    expect(profiles.findById(created.id)).toEqual(created);
  });

  it("returns null for an unknown id", () => {
    expect(createProfileRepository(db).findById("missing")).toBeNull();
  });

  it("rejects an unsupported market", () => {
    // @ts-expect-error market is a closed union
    expect(() => createProfileRepository(db).create({ market: "mars", locale: "en" })).toThrow();
  });
});

describe("consent repository", () => {
  it("records consents as an append-only log scoped to the profile", () => {
    const profiles = createProfileRepository(db);
    const consents = createConsentRepository(db);
    const alice = profiles.create({ market: "global", locale: "en" });
    const bob = profiles.create({ market: "in", locale: "en" });

    consents.grant(alice.id, { type: "biometric", version: "2026-10-01" });
    consents.grant(bob.id, { type: "research", version: "2026-10-01" });

    const aliceConsents = consents.listForProfile(alice.id);
    expect(aliceConsents).toHaveLength(1);
    expect(aliceConsents[0]?.type).toBe("biometric");
    expect(aliceConsents.every((c) => c.profileId === alice.id)).toBe(true);
  });

  it("treats a later withdrawal as revoking the consent", () => {
    const profile = createProfileRepository(db).create({ market: "in", locale: "en" });
    const consents = createConsentRepository(db);

    consents.grant(profile.id, { type: "training_data", version: "v1" });
    expect(consents.isActive(profile.id, "training_data")).toBe(true);

    consents.withdraw(profile.id, "training_data");
    expect(consents.isActive(profile.id, "training_data")).toBe(false);
    // Withdrawal appends a row; history is preserved.
    expect(consents.listForProfile(profile.id)).toHaveLength(2);
  });

  it("refuses consent for a profile that does not exist", () => {
    expect(() =>
      createConsentRepository(db).grant("nope", { type: "processing", version: "v1" }),
    ).toThrow();
  });
});
