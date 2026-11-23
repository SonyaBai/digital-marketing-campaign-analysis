"""Format money and rates from integer paise and integer counts.

Display rounding is half-up, so the figures printed by the script are the
figures used in the write-up.
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


def rupee_amount(paise: int) -> str:
    """Plain rupee string without a symbol or thousands separator, for CSV cells."""
    sign = "-" if int(paise) < 0 else ""
    whole, frac = divmod(abs(int(paise)), 100)
    return f"{sign}{whole}.{frac:02d}"


def inr(paise: int) -> str:
    sign = "-" if int(paise) < 0 else ""
    whole, frac = divmod(abs(int(paise)), 100)
    return f"{sign}₹{whole:,}.{frac:02d}"


def inr_millions(paise: int, decimals: int = 2) -> str:
    sign = "-" if int(paise) < 0 else ""
    millions = (Decimal(abs(int(paise))) / Decimal(100_000_000)).quantize(
        _quantum(decimals), rounding=ROUND_HALF_UP
    )
    return f"{sign}₹{millions}M"


def rate_pct(numerator: int, denominator: int, decimals: int = 2) -> str:
    if int(denominator) == 0:
        return "n/a"
    value = (Decimal(int(numerator)) / Decimal(int(denominator))) * Decimal(100)
    return f"{value.quantize(_quantum(decimals), rounding=ROUND_HALF_UP)}%"


def inr_per(paise: int, count: int) -> str:
    """Rupees per event (CPC, CPL, CAC, AOV), rounded half-up to the paisa."""
    if int(count) == 0:
        return "n/a"
    rupees = (Decimal(int(paise)) / Decimal(int(count))) / Decimal(100)
    rounded = rupees.quantize(_quantum(2), rounding=ROUND_HALF_UP)
    sign = "-" if rounded < 0 else ""
    return f"{sign}₹{abs(rounded):,.2f}"


def millions_float(paise: int) -> float:
    """Axis value. Label text should use inr_millions, not this float."""
    return int(paise) / 100_000_000


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
    total_spend = sum(int(value) for value in frame["spend_paise"])
    records = []
    for key, row in frame.iterrows():
        records.append(
            {
                "segment": pretty_label(key),
                "spend": inr(row.spend_paise),
                "revenue": inr(row.revenue_paise),
                "gross_profit": inr(row.gross_profit_paise),
                "romi": rate_pct(row.gross_profit_paise, row.spend_paise, 2),
                "orders": f"{int(row.orders):,}",
                "ctr": rate_pct(row.clicks, row.impressions, 3),
                "click_to_lead": rate_pct(row.leads, row.clicks, 2),
                "lead_to_order": rate_pct(row.orders, row.leads, 2),
                "cpc": inr_per(row.spend_paise, row.clicks),
                "cpl": inr_per(row.spend_paise, row.leads),
                "cac": inr_per(row.spend_paise, row.orders),
                "aov": inr_per(row.revenue_paise, row.orders),
                "spend_share": rate_pct(row.spend_paise, total_spend, 2),
            }
        )
    return pd.DataFrame.from_records(records)
