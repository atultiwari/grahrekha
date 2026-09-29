"""Pluggable providers discovered through Python entry points.

Core code asks for a provider by *name* (e.g. an ephemeris "jyotishganit" or
"swisseph") and never imports optional implementations directly. That is how the
separately licensed `adapters-agpl` package can plug in without core importing
AGPL code (docs/DECISIONS.md D-011). Packages register providers in pyproject:

    [project.entry-points."grahrekha.ephemeris"]
    swisseph = "grahrekha_adapters_agpl.swisseph:SwissEphemerisProvider"
"""

from importlib.metadata import EntryPoint, entry_points


class ProviderNotFoundError(LookupError):
    pass


def _select_entry_points(group: str) -> list[EntryPoint]:
    return list(entry_points(group=group))


def available_providers(group: str) -> list[str]:
    return sorted(ep.name for ep in _select_entry_points(group))


def load_provider(group: str, name: str) -> object:
    for ep in _select_entry_points(group):
        if ep.name == name:
            return ep.load()()
    options = ", ".join(available_providers(group)) or "none installed"
    raise ProviderNotFoundError(f"no provider {name!r} in {group!r} (available: {options})")
