"""Offline birthplace search over GeoNames (CC BY 4.0: "GeoNames, geonames.org").

Prefix search on official, ASCII and alternate names (old names like "Bombay", "Banaras",
and native scripts such as Devanagari), ranked by population. Everything is in memory; no
network (D-016). Data: cities with population > 5,000 (scripts/fetch-data.sh --only A2).
"""

import csv
import unicodedata
from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path

LATIN_LIMIT = 0x250  # Basic Latin .. Latin Extended-B
OFFICIAL, ALTERNATE = 0, 1  # match tiers: official/ASCII names rank above alternate names


@dataclass(frozen=True)
class Place:
    geoname_id: int
    name: str
    region: str  # state / province (admin1), may be ""
    country: str  # ISO 3166-1 alpha-2
    latitude: float
    longitude: float
    timezone: str
    population: int


def fold(text: str) -> str:
    """Case-fold; drop accents on Latin letters only (Devanagari vowel signs must stay)."""
    decomposed = unicodedata.normalize("NFD", unicodedata.normalize("NFKC", text).casefold())
    out: list[str] = []
    for ch in decomposed:
        if unicodedata.combining(ch) and out and ord(out[-1]) < LATIN_LIMIT:
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out)).strip()


class PlaceIndex:
    def __init__(self, places: list[Place], keys: list[tuple[str, int, int]]) -> None:
        self._places = places
        self._keys = sorted(keys)
        self._words = [k[0] for k in self._keys]

    @classmethod
    def load(cls, cities: Path, admin1: Path) -> "PlaceIndex":
        regions: dict[str, str] = {}
        with admin1.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f, delimiter="\t"):
                if len(row) >= 2:
                    regions[row[0]] = row[1]
        places: list[Place] = []
        keys: list[tuple[str, int, int]] = []
        with cities.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                if len(row) < 18:
                    continue
                index = len(places)
                places.append(
                    Place(
                        geoname_id=int(row[0]),
                        name=row[1],
                        region=regions.get(f"{row[8]}.{row[10]}", ""),
                        country=row[8],
                        latitude=float(row[4]),
                        longitude=float(row[5]),
                        timezone=row[17],
                        population=int(row[14] or 0),
                    )
                )
                official = {fold(row[1]), fold(row[2])} - {""}
                alternate = {fold(n) for n in row[3].split(",")} - official - {""}
                keys.extend((name, OFFICIAL, index) for name in official)
                keys.extend((name, ALTERNATE, index) for name in alternate)
        return cls(places, keys)

    def search(self, query: str, limit: int = 10) -> list[Place]:
        prefix = fold(query)
        if not prefix:
            return []
        best_tier: dict[int, int] = {}
        position = bisect_left(self._words, prefix)
        while position < len(self._words) and self._words[position].startswith(prefix):
            _, tier, index = self._keys[position]
            best_tier[index] = min(tier, best_tier.get(index, tier))
            position += 1
        ranked = sorted(
            best_tier,
            key=lambda i: (best_tier[i], -self._places[i].population, self._places[i].name),
        )
        return [self._places[i] for i in ranked[: max(0, limit)]]

    def __len__(self) -> int:
        return len(self._places)
