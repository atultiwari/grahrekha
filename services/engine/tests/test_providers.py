from importlib.metadata import EntryPoint
from typing import Any

import pytest

from grahrekha_engine import providers
from grahrekha_engine.providers import ProviderNotFoundError, available_providers, load_provider

GROUP = "grahrekha.test_providers"


class FakeProvider:
    name = "fake"


def _entry_points(*eps: EntryPoint) -> Any:
    def select(group: str) -> list[EntryPoint]:
        return [ep for ep in eps if ep.group == group]

    return select


@pytest.fixture
def registered(monkeypatch: pytest.MonkeyPatch) -> None:
    ep = EntryPoint(name="fake", value=f"{__name__}:FakeProvider", group=GROUP)
    monkeypatch.setattr(providers, "_select_entry_points", _entry_points(ep))


@pytest.mark.usefixtures("registered")
def test_lists_registered_providers_by_group() -> None:
    assert available_providers(GROUP) == ["fake"]
    assert available_providers("grahrekha.other") == []


@pytest.mark.usefixtures("registered")
def test_loads_and_instantiates_a_provider_by_name() -> None:
    assert isinstance(load_provider(GROUP, "fake"), FakeProvider)


@pytest.mark.usefixtures("registered")
def test_unknown_provider_error_names_the_alternatives() -> None:
    with pytest.raises(ProviderNotFoundError, match=r"'swisseph'.*available: fake"):
        load_provider(GROUP, "swisseph")
