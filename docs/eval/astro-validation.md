# Astrology engine validation (Phase 3)

**Date:** 2026-09-30
**Engine:** `services/engine/src/grahrekha_engine/astro/`, jyotishganit 0.1.3 (MIT), running fully offline.
**Reference:** Swiss Ephemeris 2.10.03 (AGPL; used only in `adapters-agpl/`, per D-011), with the Moshier ephemeris and the True Citra ayanamsa.

**Reproduce:**

```bash
cd adapters-agpl && uv run python -m grahrekha_adapters_agpl.validate_astro
```

## Results (30 reference births, 1930–2020, 12 cities on 5 continents)

| Check | Target | Result |
|---|---|---|
| Sun … Saturn sidereal longitude | < 0.05° | **≤ 0.0031°** (Moon worst; others ≤ 0.001°) ✅ |
| Rahu / Ketu (mean node) | < 0.05° | **0.0007°**, after our fix (was 0.88°) ✅ |
| Mahadasha start dates vs an independent Vimshottari implementation | < 1 day | **≤ 1 day.** The residual is start times rounded to calendar dates. Using Swiss Ephemeris's Moon instead of ours: ≤ 2 days (the 0.003° Moon difference) ✅ |
| Wartime India (1942–45 UTC+6:30), DST | correct offset | ✅ unit-tested |

**Conventions** (record these when comparing with other software):
- **Ayanamsa:** True Chitra Paksha (Spica fixed at 180°). This differs from Lahiri by a small, slowly varying amount, so JHora must be set to "True Chitra" for a like-for-like comparison.
- **Rahu/Ketu:** mean node. The true node differs by up to about 1.7°.
- **Vimshottari year:** 365.25 days (Julian).
- **Houses:** whole sign.

## Problems found in jyotishganit 0.1.3 (and how we handle them)

1. **Rahu/Ketu drift by precession.** It subtracts a J2000-referred ayanamsa (consistent with its J2000-frame planets) from a mean node referred to the equinox *of date*.
   - The resulting error is about 1.4° per century from the year 2000: 0.3° for 1980 births, about 1° for 1930 births. That is enough to change the nakshatra pada.
   - **We correct it** in `astro/chart.py`, with a regression test against Swiss Ephemeris values.
2. **Runtime download of the whole Hipparcos catalogue.** The 50 MB file is saved into the *current working directory* to read one star (Spica), using skyfield's default loader and ignoring the library's own data directory.
   - **We replace it** with Spica's frozen catalogue row (`astro/offline.py`).
   - Combined with the pinned DE421 file, the engine needs no network (D-016). The Docker CI job proves this by computing a chart inside the network-isolated container.
3. **"Current dasha" depends on the system clock.** We compute it for an explicit reference date, so results are reproducible.

**Upstream:** issues 1 and 2 are worth reporting to jyotishganit. Reporting them publicly is left to the owner's decision.

## Raw report

### Generated output

Reference births: 30 (1930-2020, 12 cities incl. India, Nepal and 4 continents).
Positions: sidereal, True Chitra ayanamsa. Tolerance: 0.05 deg; dasha boundaries: 1 day.

| Body | Worst |difference| (deg) | Within 0.05 deg |
|---|---|---|
| Sun | 0.0005 | yes |
| Moon | 0.0031 | yes |
| Mars | 0.0006 | yes |
| Mercury | 0.0009 | yes |
| Jupiter | 0.0004 | yes |
| Venus | 0.0006 | yes |
| Saturn | 0.0006 | yes |
| Rahu (mean node) | 0.0007 | yes |
| Rahu (true node) | 1.6933 | NO |

**Mahadasha start dates** vs independent formula (365.25-day years): worst 2 days; median 1 days.

| Birth (local) | Timezone | Worst dasha start difference (days) |
|---|---|---|
| 2002-10-03 20:46:00 | America/New_York | 1 |
| 1985-03-13 20:32:00 | Asia/Kolkata | 1 |
| 2005-02-08 00:03:00 | Asia/Tokyo | 1 |
| 1979-09-01 14:58:00 | America/Sao_Paulo | 1 |
| 2007-02-12 00:52:00 | America/Sao_Paulo | 1 |
| 2019-03-28 02:11:00 | Asia/Kolkata | 1 |
| 1992-08-28 02:59:00 | America/Sao_Paulo | 1 |
| 1987-10-25 02:50:00 | Europe/London | 1 |
| 1938-03-31 07:59:00 | Europe/London | 1 |
| 2020-09-26 08:28:00 | Asia/Kolkata | 1 |
| 1948-01-16 06:47:00 | Australia/Sydney | 1 |
| 1959-07-07 08:48:00 | America/Sao_Paulo | 1 |
| 2004-09-12 16:17:00 | Asia/Kathmandu | 1 |
| 1962-05-02 01:55:00 | Asia/Kolkata | 1 |
| 1937-03-19 15:42:00 | Europe/London | 2 |
| 1977-07-30 08:44:00 | Africa/Nairobi | 1 |
| 1988-09-18 23:12:00 | Asia/Kolkata | 1 |
| 1977-06-02 10:11:00 | Asia/Kathmandu | 1 |
| 1954-07-01 11:54:00 | Asia/Kolkata | 1 |
| 1975-04-16 13:53:00 | America/Sao_Paulo | 1 |
| 1979-02-11 10:30:00 | America/New_York | 1 |
| 1938-04-08 17:53:00 | Africa/Nairobi | 2 |
| 1976-11-10 22:46:00 | Asia/Kolkata | 1 |
| 1937-02-18 09:10:00 | Asia/Kolkata | 1 |
| 2000-04-20 13:44:00 | Asia/Kolkata | 1 |
| 1937-12-10 08:04:00 | Asia/Kolkata | 1 |
| 1989-02-15 11:00:00 | America/Sao_Paulo | 1 |
| 1968-07-21 16:02:00 | Asia/Kolkata | 1 |
| 1944-12-12 12:24:00 | Africa/Nairobi | 2 |
| 2003-08-28 04:54:00 | Europe/London | 1 |
