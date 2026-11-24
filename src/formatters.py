"""Format money and rates from integer US cents and integer counts.

Display rounding is half-up, so the figures printed by the script are the
figures used in the write-up. Dollars are the converted amounts; the raw
file remains in rupees.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from src.constants import (
    CAMPAIGN_LABELS,
    CATEGORY_LABELS,
    PLATFORM_LABELS,
    TARGETING_LABELS,
    TIER_LABELS,
)


def _quantum(decimals: int) -> Decimal:
    return Decimal("1").scaleb(-decimals)


def money_amount(cents: int) -> str:
    """Plain dollar string without a symbol or thousands separator, for CSV cells."""
    sign = "-" if int(cents) < 0 else ""
    whole, frac = divmod(abs(int(cents)), 100)
    return f"{sign}{whole}.{frac:02d}"


def usd(cents: int) -> str:
    sign = "-" if int(cents) < 0 else ""
    whole, frac = divmod(abs(int(cents)), 100)
    return f"{sign}${whole:,}.{frac:02d}"


def usd_thousands(cents: int, decimals: int = 2) -> str:
    """Compact label, for example $55.74k."""
    sign = "-" if int(cents) < 0 else ""
    thousands = (Decimal(abs(int(cents))) / Decimal(100_000)).quantize(
        _quantum(decimals), rounding=ROUND_HALF_UP
    )
    return f"{sign}${thousands}k"


def rate_pct(numerator: int, denominator: int, decimals: int = 2) -> str:
    if int(denominator) == 0:
        return "n/a"
    value = (Decimal(int(numerator)) / Decimal(int(denominator))) * Decimal(100)
    return f"{value.quantize(_quantum(decimals), rounding=ROUND_HALF_UP)}%"


def usd_per(cents: int, count: int) -> str:
    """Dollars per event (CPC, CPL, CAC, AOV), rounded half-up to the cent."""
    if int(count) == 0:
        return "n/a"
    dollars = (Decimal(int(cents)) / Decimal(int(count))) / Decimal(100)
    rounded = dollars.quantize(_quantum(2), rounding=ROUND_HALF_UP)
    sign = "-" if rounded < 0 else ""
    return f"{sign}${abs(rounded):,.2f}"


def thousands_float(cents: int) -> float:
    """Axis value in thousands of dollars. Labels should use usd_thousands."""
    return int(cents) / 100_000


def pretty_label(value: object) -> str:
    if isinstance(value, tuple):
        return " · ".join(pretty_label(part) for part in value)
    text = str(value)
    for mapping in (
        CAMPAIGN_LABELS,
        CATEGORY_LABELS,
        PLATFORM_LABELS,
        TARGETING_LABELS,
        TIER_LABELS,
    ):
        if text in mapping:
            return mapping[text]
    return text


def format_kpi_table(frame: pd.DataFrame) -> pd.DataFrame:
    """One display table. Money and rates are strings, so they round once."""
    total_spend = sum(int(value) for value in frame["spend_cents"])
    records = []
    for key, row in frame.iterrows():
        records.append(
            {
                "segment": pretty_label(key),
                "spend": usd(row.spend_cents),
                "revenue": usd(row.revenue_cents),
                "gross_profit": usd(row.gross_profit_cents),
                "romi": rate_pct(row.gross_profit_cents, row.spend_cents, 2),
                "orders": f"{int(row.orders):,}",
                "ctr": rate_pct(row.clicks, row.impressions, 3),
                "click_to_lead": rate_pct(row.leads, row.clicks, 2),
                "lead_to_order": rate_pct(row.orders, row.leads, 2),
                "cpc": usd_per(row.spend_cents, row.clicks),
                "cpl": usd_per(row.spend_cents, row.leads),
                "cac": usd_per(row.spend_cents, row.orders),
                "aov": usd_per(row.revenue_cents, row.orders),
                "spend_share": rate_pct(row.spend_cents, total_spend, 2),
            }
        )
    return pd.DataFrame.from_records(records)
