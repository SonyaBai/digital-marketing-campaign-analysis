"""Load and clean the February 2021 marketing extract.

The source file is a balanced panel: 11 campaigns, 28 days, one row per
campaign-day, no missing values, and a funnel that never runs backwards
(clicks do not exceed impressions, leads do not exceed clicks, orders do
not exceed leads).

The one campaign-name defect is casing. ``facebOOK_tier2`` (campaign_id
348934, all 28 days) is the same campaign as the lowercase pattern used by
every other name. Lowercasing fixes it. The original text is kept on
``campaign_name_raw``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

from src.constants import (
    INR_PER_USD,
    PLATFORM_BY_CAMPAIGN,
    RAW_COLUMNS,
    TARGETING_BY_CAMPAIGN,
    TIER_BY_CAMPAIGN,
)

MONEY_COLUMNS = ("mark_spent", "revenue")
INT_COLUMNS = ("id", "campaign_id", "impressions", "clicks", "leads", "orders")


def load_raw(path: Path | str) -> pd.DataFrame:
    """Read the source CSV. Money stays as text so paise are exact."""
    frame = pd.read_csv(path, dtype=str)
    missing = [column for column in RAW_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Raw file is missing columns: {missing}")
    return frame.loc[:, list(RAW_COLUMNS)].copy()


def describe_cleaning(raw: pd.DataFrame) -> dict[str, object]:
    names = raw["campaign_name"].str.strip()
    mask = names != names.str.lower()
    return {
        "rows": int(len(raw)),
        "blank_cells": int(raw.isna().sum().sum() + (raw == "").sum().sum()),
        "normalized_name_rows": int(mask.sum()),
        "normalized_names": sorted(names.loc[mask].unique().tolist()),
        "whitespace_name_rows": int((raw["campaign_name"] != names).sum()),
    }


def _to_paise(value: object) -> int:
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        raise ValueError("Missing money value.")
    amount = Decimal(text)
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _paise_to_cents(paise: int) -> int:
    """Convert rupee paise to US cents at the fixed February 2021 rate.

    One paisa and one cent are both a hundredth of the major unit, so
    cents = paise / INR_PER_USD. Each campaign-day is rounded half-up to
    the cent. Totals are sums of those cents.
    """
    return int((Decimal(int(paise)) / INR_PER_USD).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def clean_marketing(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the analysis table, one row per source row, with derived fields.

    Spend and revenue are converted from rupees to US dollars at
    ``INR_PER_USD`` and stored as integer cents. Each campaign-day is
    rounded half-up to the cent. Gross profit is the difference of those
    cents, not a second conversion. Aggregations should sum the cent
    columns. Row-level rates are not stored: several days have zero leads
    or zero orders, and the KPIs in this project are ratios of sums.
    """
    frame = raw.copy()
    frame["campaign_name_raw"] = frame["campaign_name"].str.strip()
    frame["campaign_name"] = frame["campaign_name_raw"].str.lower()
    frame["category"] = frame["category"].str.strip().str.lower()

    for column in INT_COLUMNS:
        frame[column] = frame[column].str.strip().astype(int)

    frame["mark_spent_paise"] = frame["mark_spent"].map(_to_paise).astype("int64")
    frame["revenue_paise"] = frame["revenue"].map(_to_paise).astype("int64")
    frame["c_date"] = pd.to_datetime(frame["c_date"].str.strip(), format="%Y-%m-%d")

    unknown = sorted(set(frame["campaign_name"]) - set(PLATFORM_BY_CAMPAIGN))
    if unknown:
        raise ValueError(f"No platform/targeting map for campaigns: {unknown}")

    frame["platform"] = frame["campaign_name"].map(PLATFORM_BY_CAMPAIGN)
    frame["city_tier"] = frame["campaign_name"].map(TIER_BY_CAMPAIGN).fillna("not_tiered")
    frame["targeting"] = frame["campaign_name"].map(TARGETING_BY_CAMPAIGN)
    frame["weekday"] = frame["c_date"].dt.day_name()
    frame["is_weekend"] = (frame["c_date"].dt.day_of_week >= 5).astype(int)
    frame["gross_profit_paise"] = frame["revenue_paise"] - frame["mark_spent_paise"]
    _validate(frame)

    frame["spend_cents"] = frame["mark_spent_paise"].map(_paise_to_cents).astype("int64")
    frame["revenue_cents"] = frame["revenue_paise"].map(_paise_to_cents).astype("int64")
    frame["gross_profit_cents"] = frame["revenue_cents"] - frame["spend_cents"]

    columns = [
        "id",
        "c_date",
        "campaign_name",
        "campaign_name_raw",
        "category",
        "campaign_id",
        "platform",
        "city_tier",
        "targeting",
        "impressions",
        "spend_cents",
        "clicks",
        "leads",
        "orders",
        "revenue_cents",
        "gross_profit_cents",
        "weekday",
        "is_weekend",
    ]
    return frame.loc[:, columns].sort_values(["c_date", "id"]).reset_index(drop=True)


def export_frame(clean: pd.DataFrame) -> pd.DataFrame:
    """CSV-ready frame. Money is US dollars, written from integer cents."""
    from src.formatters import money_amount

    out = pd.DataFrame(
        {
            "id": clean["id"].astype(int),
            "c_date": clean["c_date"].dt.strftime("%Y-%m-%d"),
            "campaign_name": clean["campaign_name"],
            "campaign_name_raw": clean["campaign_name_raw"],
            "category": clean["category"],
            "campaign_id": clean["campaign_id"].astype(int),
            "platform": clean["platform"],
            "city_tier": clean["city_tier"],
            "targeting": clean["targeting"],
            "impressions": clean["impressions"].astype(int),
            "mark_spent": clean["spend_cents"].map(money_amount),
            "clicks": clean["clicks"].astype(int),
            "leads": clean["leads"].astype(int),
            "orders": clean["orders"].astype(int),
            "revenue": clean["revenue_cents"].map(money_amount),
            "gross_profit": clean["gross_profit_cents"].map(money_amount),
            "weekday": clean["weekday"],
            "is_weekend": clean["is_weekend"].astype(int),
        }
    )
    return out


def _validate(frame: pd.DataFrame) -> None:
    if len(frame) != 308:
        raise ValueError(f"Expected 308 campaign-days, found {len(frame)}.")
    if frame["campaign_name"].nunique() != 11:
        raise ValueError("Expected 11 campaigns after cleaning.")
    if frame["c_date"].nunique() != 28:
        raise ValueError("Expected 28 dates.")
    if frame["c_date"].min() != pd.Timestamp("2021-02-01") or frame["c_date"].max() != pd.Timestamp("2021-02-28"):
        raise ValueError("Dates are outside February 2021.")
    if pd.Timestamp("2021-02-01").day_name() != "Monday":
        raise ValueError("Weekday numbering is not Monday-first.")
    if int(frame.duplicated(["c_date", "campaign_name"]).sum()) != 0:
        raise ValueError("Duplicate campaign-days.")
    if int((frame["campaign_name"] != frame["campaign_name"].str.lower()).sum()) != 0:
        raise ValueError("Campaign names were not lowercased.")

    if int(frame["mark_spent_paise"].sum()) != 3_059_087_982 or int(frame["revenue_paise"].sum()) != 4_288_936_600:
        raise ValueError("Raw rupee totals do not match the published extract.")
    if int((frame["impressions"] <= 0).sum()) or int((frame["mark_spent_paise"] <= 0).sum()):
        raise ValueError("Impressions and spend must be positive.")
    if int((frame["clicks"] > frame["impressions"]).sum()):
        raise ValueError("Clicks exceed impressions.")
    if int((frame["leads"] > frame["clicks"]).sum()):
        raise ValueError("Leads exceed clicks.")
    if int((frame["orders"] > frame["leads"]).sum()):
        raise ValueError("Orders exceed leads.")
    zeros_agree = np.array_equal(
        frame["orders"].to_numpy() == 0,
        frame["revenue_paise"].to_numpy() == 0,
    )
    if not zeros_agree:
        raise ValueError("Orders and revenue disagree on which rows are zero.")

    cased = frame.loc[frame["campaign_name_raw"] != frame["campaign_name"], "campaign_name_raw"]
    if sorted(cased.unique().tolist()) != ["facebOOK_tier2"] or len(cased) != 28:
        raise ValueError("The casing quirk is not the expected 28 facebOOK_tier2 rows.")
    tier2_ids = frame.loc[frame["campaign_name"] == "facebook_tier2", "campaign_id"].unique()
    if list(tier2_ids) != [348934]:
        raise ValueError("facebook_tier2 is not campaign_id 348934.")
