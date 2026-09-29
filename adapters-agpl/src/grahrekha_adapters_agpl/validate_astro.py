"""Validate the default astrology engine (jyotishganit) against Swiss Ephemeris (AGPL).

Usage (from adapters-agpl/):
  uv run python -m grahrekha_adapters_agpl.validate_astro [--out ../docs/eval/astro-validation.md]

Swiss Ephemeris is the de facto standard behind JHora/PyJHora. Planet positions use its
True Chitra ayanamsa (the one jyotishganit uses) and the built-in Moshier ephemeris (no
data files; ~arcsecond accuracy, far below our tolerance). Dasha dates come from an
independent implementation of the Vimshottari formula.

Targets (docs/IMPLEMENTATION-PLAN.md 3.4): planet longitude < 0.05 deg; dasha boundary < 1 day.
"""

import argparse
import random
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import swisseph as swe
from grahrekha_engine.astro.chart import compute_chart
from grahrekha_engine.astro.timezones import timezone_for, utc_offset_hours
from grahrekha_engine.contracts.astro import BirthDataV1

EPHEMERIS = (
    Path(__file__).resolve().parents[3] / "services/engine/models/weights/A1-de421/de421.bsp"
)
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = dict(zip(DASHA_ORDER, [7, 20, 6, 10, 7, 18, 16, 19, 17], strict=True))
NAKSHATRA_DEG = 360 / 27
CITIES = [
    ("Delhi", 28.61, 77.21),
    ("Mumbai", 19.08, 72.88),
    ("Kolkata", 22.57, 88.36),
    ("Chennai", 13.08, 80.27),
    ("Varanasi", 25.32, 82.97),
    ("Kathmandu", 27.72, 85.32),
    ("London", 51.51, -0.13),
    ("New York", 40.71, -74.01),
    ("Sydney", -33.87, 151.21),
    ("Sao Paulo", -23.55, -46.63),
    ("Nairobi", -1.29, 36.82),
    ("Tokyo", 35.68, 139.69),
]


def reference_births(n: int = 30, seed: int = 20260930) -> list[BirthDataV1]:
    rng = random.Random(seed)
    births = []
    for _ in range(n):
        _, lat, lon = rng.choice(CITIES)
        day = date(1930, 1, 1) + timedelta(
            days=rng.randrange((date(2020, 12, 31) - date(1930, 1, 1)).days)
        )
        births.append(
            BirthDataV1(
                birth_date=day,
                birth_time=time(rng.randrange(24), rng.randrange(60)),
                time_confidence="exact",
                latitude=lat,
                longitude=lon,
            )
        )
    return births


def _julian_day_ut(moment: datetime) -> float:
    hours = moment.hour + moment.minute / 60 + moment.second / 3600
    return float(swe.julday(moment.year, moment.month, moment.day, hours))


def swiss_longitudes(moment_utc: datetime) -> dict[str, float]:
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
    jd = _julian_day_ut(moment_utc)
    flags = swe.FLG_SIDEREAL | swe.FLG_MOSEPH
    out = {name: float(swe.calc_ut(jd, body, flags)[0][0]) for name, body in PLANETS.items()}
    out["Rahu (mean node)"] = float(swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0])
    out["Rahu (true node)"] = float(swe.calc_ut(jd, swe.TRUE_NODE, flags)[0][0])
    return out


def vimshottari(
    moon_longitude: float, birth_utc: datetime, days_per_year: float = 365.25
) -> list[tuple[str, date]]:
    """Mahadasha start dates from the standard formula (independent implementation)."""
    index = int(moon_longitude // NAKSHATRA_DEG)
    lord = DASHA_ORDER[index % 9]
    remaining = 1 - (moon_longitude % NAKSHATRA_DEG) / NAKSHATRA_DEG
    first_start = birth_utc - timedelta(days=(1 - remaining) * DASHA_YEARS[lord] * days_per_year)
    starts, cursor, position = [], first_start, DASHA_ORDER.index(lord)
    for step in range(9):
        current = DASHA_ORDER[(position + step) % 9]
        starts.append((current, cursor.date()))
        cursor += timedelta(days=DASHA_YEARS[current] * days_per_year)
    return starts


def _angle_diff(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def validate(births: list[BirthDataV1]) -> str:
    worst: dict[str, float] = {}
    dasha_days: list[int] = []
    rows = []
    for birth in births:
        assert birth.birth_time is not None
        zone = timezone_for(birth.latitude, birth.longitude)
        offset = utc_offset_hours(birth.birth_date, birth.birth_time, zone)
        utc = datetime.combine(birth.birth_date, birth.birth_time) - timedelta(hours=offset)
        ours = compute_chart(birth, EPHEMERIS, reference_date=date(2026, 9, 30))
        swiss = swiss_longitudes(utc.replace(tzinfo=UTC))
        ours_by = {p.planet: p.longitude for p in ours.planets}
        for name in PLANETS:
            worst[name] = max(worst.get(name, 0.0), _angle_diff(ours_by[name], swiss[name]))
        for node in ("Rahu (mean node)", "Rahu (true node)"):
            worst[node] = max(worst.get(node, 0.0), _angle_diff(ours_by["Rahu"], swiss[node]))
        expected = vimshottari(swiss["Moon"], utc)
        ours_starts = {p.lord: p.start for p in ours.mahadashas}
        diffs = [
            abs((ours_starts[lord] - start).days) for lord, start in expected if lord in ours_starts
        ]
        dasha_days.append(max(diffs))
        rows.append(f"| {birth.birth_date} {birth.birth_time} | {zone} | {max(diffs)} |")

    lines = [
        "# Astrology engine validation: jyotishganit vs Swiss Ephemeris",
        "",
        f"Reference births: {len(births)} (1930-2020, 12 cities incl. India, Nepal and 4 continents).",
        "Positions: sidereal, True Chitra ayanamsa. Tolerance: 0.05 deg; dasha boundaries: 1 day.",
        "",
        "| Body | Worst |difference| (deg) | Within 0.05 deg |",
        "|---|---|---|",
    ]
    lines += [f"| {k} | {v:.4f} | {'yes' if v < 0.05 else 'NO'} |" for k, v in worst.items()]
    lines += [
        "",
        (
            "**Mahadasha start dates** vs independent formula (365.25-day years): "
            f"worst {max(dasha_days)} days; median {sorted(dasha_days)[len(dasha_days) // 2]} days."
        ),
        "",
        "| Birth (local) | Timezone | Worst dasha start difference (days) |",
        "|---|---|---|",
        *rows,
    ]
    return "\n".join(lines) + "\n"


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = validate(reference_births())
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":  # pragma: no cover
    main()
