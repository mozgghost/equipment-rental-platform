"""Pure pricing rules; intentionally independent of Django for fast unit tests."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

CENT = Decimal("0.01")
ZERO = Decimal("0.00")

@dataclass(frozen=True)
class PriceQuote:
    amount: Decimal
    deposit: Decimal
    currency: str
    billable_units: int
    unit_rate: Decimal
    billing_unit: str

def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)

def quote_rental(*, starts_at: datetime, ends_at: datetime, rate: Decimal, billing_unit: str,
                 deposit: Decimal, currency: str = "EUR", minimum_hours: int = 1) -> PriceQuote:
    if starts_at.utcoffset() is None or ends_at.utcoffset() is None:
        raise ValueError("Rental timestamps must be timezone-aware")
    if ends_at <= starts_at:
        raise ValueError("Rental end must be after its start")
    if not rate.is_finite() or not deposit.is_finite():
        raise ValueError("Rates and deposits must be finite decimal amounts")
    if rate < ZERO or deposit < ZERO:
        raise ValueError("Rates and deposits cannot be negative")
    # Normalize to UTC so a rental crossing a DST transition is measured as elapsed time,
    # not as wall-clock arithmetic in a local timezone.
    start_utc = starts_at.astimezone(timezone.utc)
    end_utc = ends_at.astimezone(timezone.utc)
    duration_seconds = Decimal(str((end_utc - start_utc).total_seconds()))
    duration_hours = duration_seconds / Decimal("3600")
    if duration_hours < Decimal(minimum_hours):
        raise ValueError("Rental is shorter than the minimum duration")
    if billing_unit == "hour":
        units = int(duration_hours.to_integral_value(rounding=ROUND_CEILING))
    elif billing_unit == "day":
        units = int((duration_seconds / Decimal("86400")).to_integral_value(rounding=ROUND_CEILING))
    else:
        raise ValueError("Unsupported billing unit")
    return PriceQuote(money(rate * units), money(deposit), currency.upper(), units, money(rate), billing_unit)
