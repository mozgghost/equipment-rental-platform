from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from apps.bookings.domain.pricing import quote_rental


def test_hourly_quote_rounds_duration_up_to_whole_billable_hours():
    start = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    quote = quote_rental(starts_at=start, ends_at=start + timedelta(hours=1, minutes=1),
        rate=Decimal("12.50"), billing_unit="hour", deposit=Decimal("125.00"))
    assert quote.billable_units == 2
    assert quote.amount == Decimal("25.00")
    assert quote.deposit == Decimal("125.00")
    assert quote.currency == "EUR"


def test_daily_quote_rounds_partial_day_up():
    start = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    quote = quote_rental(starts_at=start, ends_at=start + timedelta(hours=25),
        rate=Decimal("99.95"), billing_unit="day", deposit=Decimal("0.00"), currency="eur")
    assert quote.billable_units == 2
    assert quote.amount == Decimal("199.90")
    assert quote.currency == "EUR"


def test_rejects_naive_timestamps():
    start = datetime(2026, 11, 1, 8)
    with pytest.raises(ValueError, match="timezone-aware"):
        quote_rental(starts_at=start, ends_at=start + timedelta(hours=1), rate=Decimal("10"),
            billing_unit="hour", deposit=Decimal("0"))


@pytest.mark.parametrize("end_delta", [timedelta(0), timedelta(hours=-1)])
def test_rejects_empty_or_negative_duration(end_delta):
    start = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="after its start"):
        quote_rental(starts_at=start, ends_at=start + end_delta, rate=Decimal("10"),
            billing_unit="hour", deposit=Decimal("0"))


def test_rejects_below_minimum_rental_duration():
    start = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="minimum duration"):
        quote_rental(starts_at=start, ends_at=start + timedelta(minutes=30),
            rate=Decimal("10"), billing_unit="hour", deposit=Decimal("0"), minimum_hours=1)


def test_negative_amounts_are_rejected():
    start = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="cannot be negative"):
        quote_rental(starts_at=start, ends_at=start + timedelta(hours=1), rate=Decimal("-0.01"),
            billing_unit="hour", deposit=Decimal("0"))


def test_non_finite_money_is_rejected():
    start = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="finite decimal"):
        quote_rental(starts_at=start, ends_at=start + timedelta(hours=1), rate=Decimal("NaN"),
            billing_unit="hour", deposit=Decimal("0"))


def test_duration_counts_elapsed_time_across_daylight_saving_transition():
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Europe/Amsterdam")
    start = datetime(2026, 3, 29, 1, 30, tzinfo=zone)
    end = datetime(2026, 3, 29, 3, 30, tzinfo=zone)
    quote = quote_rental(starts_at=start, ends_at=end, rate=Decimal("10.00"),
        billing_unit="hour", deposit=Decimal("0.00"))
    assert quote.billable_units == 1
    assert quote.amount == Decimal("10.00")
