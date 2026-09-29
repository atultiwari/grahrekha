from datetime import UTC, datetime

from grahrekha_adapters_agpl.validate_astro import DASHA_ORDER, vimshottari


def test_cycle_order_and_total_length() -> None:
    starts = vimshottari(0.0, datetime(2000, 1, 1, tzinfo=UTC))
    assert [lord for lord, _ in starts] == DASHA_ORDER  # Ashwini (0 deg) -> Ketu first
    # 103 years x 365.25 = 37620.75 days; calendar dates truncate the fraction.
    assert abs((starts[-1][1] - starts[0][1]).days - (120 - 17) * 365.25) <= 1


def test_balance_at_birth_uses_the_moons_position_in_its_nakshatra() -> None:
    birth = datetime(2000, 1, 1, tzinfo=UTC)
    halfway = vimshottari(360 / 27 / 2, birth)  # Moon halfway through Ashwini
    elapsed_days = (birth.date() - halfway[0][1]).days
    assert abs(elapsed_days - 3.5 * 365.25) <= 1  # half of Ketu's 7 years already elapsed
