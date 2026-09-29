# jyotishganit 0.1.3: issues found, how to verify them, and possible fixes

**Date:** 2026-09-30
**Status:** internal analysis for the owner. **Nothing has been reported upstream.** The owner decides whether and how to report it.
**Library:** [jyotishganit](https://pypi.org/project/jyotishganit/) 0.1.3 (MIT), our default astrology provider (D-005).
**Our workarounds:** `services/engine/src/grahrekha_engine/astro/chart.py` (issue 1), `astro/offline.py` (issue 2), `compute_chart(reference_date=...)` (issue 3).

| # | Issue | Severity | Who is affected |
|---|---|---|---|
| 1 | Rahu/Ketu longitude is off by the precession since J2000 (up to ~1.4° for 1900 births) | **High** for correctness | Every chart not born near the year 2000 |
| 2 | The first chart downloads the Hipparcos star catalogue (~50 MB) from the internet into the current directory | Medium (privacy, offline use, reproducibility) | Offline, sandboxed and server deployments |
| 3 | "Current" dasha uses the machine clock (`datetime.now()`, naive local time) | Low to medium (reproducibility) | Anyone storing or testing results |

---

## Issue 1: Rahu/Ketu drift by the precession since 2000

### What happens

In `jyotishganit/core/astronomical.py` (around lines 268–272):

```python
T = (t.tt - 2451545.0) / 36525.0
rahu_tropical = (125.04452 - 1934.136261 * T) % 360   # Meeus mean node
rahu_sidereal = tropical_to_sidereal(rahu_tropical, ayanamsa)
```

The two quantities are referred to different equinoxes:
- **Meeus's mean-node formula** gives a longitude measured from the **mean equinox of date**.
- **The ayanamsa** (`calculate_ayanamsa`) comes from Spica's position via Skyfield's `position.ecliptic_latlon()`, which by default uses the **J2000 ecliptic and equinox**. The planets use the same J2000 frame, so the planets are correct. Only the nodes mix frames.

Subtracting a J2000 ayanamsa from an of-date longitude leaves an error equal to the **general precession between J2000 and the birth date**. That is about 50.3″ per year, or 1.40° per century: nodes come out too small before 2000 and too large after.

### Measured (Swiss Ephemeris mean node, True Citra ayanamsa, vs jyotishganit)

| Date (noon UT) | jyotishganit Rahu | Swiss Ephemeris | Difference | Precession since J2000 |
|---|---|---|---|---|
| 1900-01-01 | 235.2869° | 236.6852° | +1.398° | 1.397° |
| 1936-01-01 | 259.0512° | 259.9457° | +0.894° | 0.894° |
| 1970-01-01 | 321.4186° | 321.8377° | +0.419° | 0.419° |
| 2000-01-01 | 101.2045° | 101.2045° | 0.000° | 0.000° |
| 2030-01-01 | 240.9373° | 240.5185° | −0.419° | −0.419° |
| 2050-01-01 | 214.1102° | 213.4124° | −0.698° | −0.699° |

The difference matches the IAU 2006 precession to about 0.001° at every date, which is why we're confident about the cause. With our correction, the worst node error over 30 reference charts (1930–2020) is **0.0007°** (`docs/eval/astro-validation.md`).

### Why it matters

For someone born in 1936 (0.89° error):
- Rahu's **nakshatra pada** (3°20′ wide) is wrong in about 27% of charts.
- Rahu's **sign** (and so its house) is wrong in about 3%.
- Ketu is affected the same way.

Anything built on the nodes inherits this: D9 placement, yogas involving Rahu/Ketu, and aspects. Dashas are not affected, because they come from the Moon, which is correct.

### How to verify

1. **Without AGPL code:**
   - Compute a chart for 1900-01-01 12:00 UT with jyotishganit and read Rahu.
   - Take the Meeus node minus the precession since J2000 (IAU 2006: `5028.796195″·T + 1.1054348″·T²`), then subtract jyotishganit's own ayanamsa.
   - The two differ by exactly the precession.
2. **Against Swiss Ephemeris** (AGPL, only inside `adapters-agpl/`, per D-011):
   ```bash
   cd adapters-agpl && uv run python -m grahrekha_adapters_agpl.validate_astro
   ```
   This reports the worst Rahu difference over 30 charts. To see the raw bug, temporarily bypass `_corrected_node` in `chart.py`: the difference returns to about 0.88°.
3. **In our test suite:** `services/engine/tests/astro/test_chart.py::test_rahu_is_corrected_for_precession`.

### Possible fixes

Ranked by how well each fixes the root cause:

1. **Put the node in the J2000 frame before subtracting the ayanamsa** (smallest change; this is what we do):
   ```python
   precession = (5028.796195 * T + 1.1054348 * T**2) / 3600.0   # degrees, IAU 2006
   rahu_tropical_j2000 = (125.04452 - 1934.136261 * T - precession) % 360
   ```
2. **Use an of-date frame consistently:** compute the ayanamsa and the planets with `ecliptic_latlon(epoch='date')`. This is conceptually cleaner, but it changes every planet by a tiny amount (nutation), so the maintainers would need to decide on it.
3. **Offer a true node option:** the mean node differs from the true node by up to about 1.7°. Many Jyotish programs let the user choose.

**Suggested upstream test:** compare Rahu against a table of reference values for dates far from 2000 (1900, 2100). Tests anchored near 2000 cannot see this bug.

---

## Issue 2: the Hipparcos catalogue is downloaded at runtime

### What happens

`_get_spica()` (in `core/astronomical.py`) and `get_spica_star_object()` (in `components/panchanga.py`) call:

```python
with load.open(hipparcos.URL) as f:
    df = hipparcos.load_dataframe(f)
```

On the first chart this downloads `hip_main.dat` (about 50 MB) from the internet and caches it in the process's **current working directory**. Only one star is needed: Spica, HIP 65474.

### Why it matters

- It fails in offline and sandboxed environments. Our engine has no internet by design (D-016).
- It leaks a network request on first use, and it writes a large file wherever the process happens to run.
- Results depend on the catalogue file that gets fetched.

### How to verify

- In an empty directory with networking disabled, run `calculate_birth_chart(...)`: it raises a network error.
- With networking enabled, `hip_main.dat` appears in the current directory.

### Possible fixes

1. **Ship Spica's catalogue row as a constant.** It is one star with fixed J1991.25 astrometry. We do this in `astro/offline.py`:
   - RA 201.29835230°, Dec −11.16124491°
   - parallax 12.44 mas
   - proper motion −42.50 / −31.73 mas/yr
2. Or let callers pass a loader or data directory, and cache under a user cache directory instead of the current one.
3. The DE421 ephemeris has the same pattern. Accept an explicit ephemeris path; our `configure_offline(ephemeris_path)` does this.

---

## Issue 3: the "current" dasha uses the system clock

### What happens

In `dasha/vimshottari.py` (around line 294):

```python
current_time = datetime.now()
```

This is naive local time on the machine running the code, and it is compared with dasha boundaries computed from the birth data.

### Why it matters

- The same birth data gives different "current dasha" answers on different days, servers or time zones.
- Stored readings can't be reproduced, and tests that assert the current dasha break over time.

### How to verify

Compute the same chart with the system clock set to two dates on either side of an antardasha boundary (or monkeypatch `datetime`): `current` changes while all the inputs are identical.

### Possible fixes

- Add an optional `reference_date` (or `at=`) parameter that defaults to "now in UTC".
- Document that `all_periods` does not depend on the clock.

We ignore jyotishganit's `current` and compute the current dasha ourselves for an explicit reference date (`compute_chart(..., reference_date=...)`).

---

## If the owner decides to report

- **Issue 1** is the most valuable. It is a clear correctness bug with a one-line fix and a reproducible table (above).
- **Issues 2 and 3** are feature requests (an offline data option; a reference date) rather than bugs.
- **Licensing note:** the Swiss Ephemeris comparison is AGPL tooling. For an upstream report, the self-contained precession check (verification step 1) is enough and needs no AGPL code.
