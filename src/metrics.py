"""KPI tables. Every rate is a ratio of sums, never an average of daily rates.

Money stays in integer paise until a formatter prints it. Gross profit is
revenue minus media spend. The file has no cost of goods, so this is not
accounting gross profit.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from src.constants import (
    HOLD_CAMPAIGNS,
    PAUSE_CAMPAIGNS,
    REALLOCATION_WEIGHTS,
    TEST_CAMPAIGNS,
    WEEKDAY_ORDER,
)


def _kpi(part: pd.DataFrame) -> dict[str, int | float]:
    impressions = int(part["impressions"].sum())
    clicks = int(part["clicks"].sum())
    leads = int(part["leads"].sum())
    orders = int(part["orders"].sum())
    spend_paise = int(part["mark_spent_paise"].sum())
    revenue_paise = int(part["revenue_paise"].sum())
    gross_profit_paise = revenue_paise - spend_paise
    days = int(part["c_date"].nunique())
    return {
        "impressions": impressions,
        "clicks": clicks,
        "leads": leads,
        "orders": orders,
        "days": days,
        "spend_paise": spend_paise,
        "revenue_paise": revenue_paise,
        "gross_profit_paise": gross_profit_paise,
        "romi": gross_profit_paise / spend_paise,
        "ctr": clicks / impressions,
        "conv1": leads / clicks,
        "conv2": (orders / leads) if leads else float("nan"),
        "cpm": (spend_paise / 100) / impressions * 1000,
    }


def aggregate(frame: pd.DataFrame, by: str | list[str] | None = None) -> pd.DataFrame:
    work = frame if by is not None else frame.assign(_segment="portfolio")
    keys = "_segment" if by is None else by
    rows = []
    index = []
    for key, part in work.groupby(keys, sort=False, dropna=False):
        index.append(key)
        rows.append(_kpi(part))
    if isinstance(keys, list):
        result_index = pd.MultiIndex.from_tuples(index, names=keys)
    else:
        result_index = pd.Index(index, name=keys)
    return pd.DataFrame(rows, index=result_index)


def _ordered(frame: pd.DataFrame, order: list[object] | tuple[object, ...]) -> pd.DataFrame:
    return frame.reindex(order)


def build_reallocation(campaign: pd.DataFrame) -> dict[str, object]:
    """Pause four loss-makers, and price one way to test the freed budget.

    The pause case spends the freed money on nothing. It uses only observed
    rows, so it does not assume a campaign can be scaled.

    The reallocation case puts that money back into four stronger campaigns
    at the ROMI each one posted in February. That is an upper bound: a larger
    budget can raise CPC and exhaust the retargeting pool.
    """
    weights = [(name, Decimal(weight)) for name, weight in REALLOCATION_WEIGHTS]
    weight_total = sum(weight for _, weight in weights)
    if weight_total != Decimal("1"):
        raise ValueError(f"Reallocation weights sum to {weight_total}, not 1.")

    named = set(PAUSE_CAMPAIGNS) | set(TEST_CAMPAIGNS) | set(HOLD_CAMPAIGNS) | {name for name, _ in weights}
    if named != set(campaign.index):
        raise ValueError(f"Campaign actions do not cover the book: {named ^ set(campaign.index)}")

    freed_paise = sum(int(campaign.loc[name, "spend_paise"]) for name in PAUSE_CAMPAIGNS)
    remaining = freed_paise
    allocations: list[dict[str, object]] = []
    for position, (name, weight) in enumerate(weights):
        if position == len(weights) - 1:
            added = remaining
        else:
            added = int((Decimal(freed_paise) * weight).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            remaining -= added
        spend_paise = int(campaign.loc[name, "spend_paise"])
        profit_paise = int(campaign.loc[name, "gross_profit_paise"])
        orders = int(campaign.loc[name, "orders"])
        romi = Decimal(profit_paise) / Decimal(spend_paise)
        incremental = (Decimal(added) / Decimal(100)) * romi
        projected_orders = (Decimal(added) / Decimal(spend_paise)) * Decimal(orders)
        allocations.append(
            {
                "campaign": name,
                "weight": weight,
                "added_spend_paise": added,
                "observed_romi": romi,
                "incremental_gross_profit": incremental.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "projected_orders": projected_orders.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            }
        )
    if sum(int(row["added_spend_paise"]) for row in allocations) != freed_paise:
        raise ValueError("Allocated paise do not equal the freed budget.")
    incremental_total = sum((row["incremental_gross_profit"] for row in allocations), Decimal("0"))

    paused_revenue = sum(int(campaign.loc[name, "revenue_paise"]) for name in PAUSE_CAMPAIGNS)
    paused_orders = sum(int(campaign.loc[name, "orders"]) for name in PAUSE_CAMPAIGNS)
    kept = campaign.drop(index=list(PAUSE_CAMPAIGNS))
    kept_spend = int(kept["spend_paise"].sum())
    kept_revenue = int(kept["revenue_paise"].sum())
    kept_orders = int(kept["orders"].sum())
    kept_profit = kept_revenue - kept_spend

    actions = {}
    for name in campaign.index:
        if name in PAUSE_CAMPAIGNS:
            actions[name] = "pause"
        elif name in TEST_CAMPAIGNS:
            actions[name] = "test"
        elif name in HOLD_CAMPAIGNS:
            actions[name] = "hold"
        else:
            actions[name] = "scale"

    return {
        "actions": actions,
        "allocations": allocations,
        "freed_spend_paise": freed_paise,
        "forgone_revenue_paise": paused_revenue,
        "forgone_orders": paused_orders,
        "forgone_profit_paise": paused_revenue - freed_paise,
        "pause_only_spend_paise": kept_spend,
        "pause_only_revenue_paise": kept_revenue,
        "pause_only_profit_paise": kept_profit,
        "pause_only_orders": kept_orders,
        "incremental_gross_profit": incremental_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


def build_report(clean: pd.DataFrame) -> dict[str, object]:
    campaign = aggregate(clean, "campaign_name").sort_values("romi", ascending=False)
    category = aggregate(clean, "category").sort_values("romi", ascending=False)
    platform = aggregate(clean, "platform").sort_values("romi", ascending=False)
    targeting = aggregate(clean, "targeting").sort_values("romi", ascending=False)

    tier_rows = clean.loc[clean["city_tier"] != "not_tiered"]
    tier = aggregate(tier_rows, "city_tier")
    tier = _ordered(tier, ["tier1", "tier2"])
    tier_platform = aggregate(tier_rows, ["platform", "city_tier"]).sort_index()

    weekend = aggregate(clean.assign(day_type=clean["is_weekend"].map({0: "Weekday", 1: "Weekend"})), "day_type")
    weekend = _ordered(weekend, ["Weekday", "Weekend"])

    weekday = aggregate(clean, "weekday")
    weekday = _ordered(weekday, WEEKDAY_ORDER)

    daily = aggregate(clean, "c_date").sort_index()
    daily["is_weekend"] = clean.groupby("c_date")["is_weekend"].max()

    half_key = clean["c_date"].dt.day.map(lambda day: "Feb 1-14" if day <= 14 else "Feb 15-28")
    half = aggregate(clean.assign(half=half_key), "half")
    half = _ordered(half, ["Feb 1-14", "Feb 15-28"])

    ex_banner = aggregate(clean.loc[clean["campaign_name"] != "banner_partner"])
    overall = aggregate(clean)

    corr_spend_romi = float(daily["spend_paise"].corr(pd.Series(daily["romi"], index=daily.index)))
    corr_spend_orders = float(daily["spend_paise"].corr(daily["orders"]))

    banner_impressions = int(clean.loc[clean["campaign_name"] == "banner_partner", "impressions"].sum())
    total_impressions = int(clean["impressions"].sum())
    youtube_profit = int(campaign.loc["youtube_blogger", "gross_profit_paise"])
    total_profit = int(overall.iloc[0]["gross_profit_paise"])

    best_day = daily["romi"].idxmax()
    worst_day = daily["romi"].idxmin()
    peak_day = daily["spend_paise"].idxmax()

    return {
        "overall": overall,
        "ex_banner": ex_banner,
        "campaign": campaign,
        "category": category,
        "platform": platform,
        "targeting": targeting,
        "tier": tier,
        "tier_platform": tier_platform,
        "weekend": weekend,
        "weekday": weekday,
        "daily": daily,
        "half": half,
        "reallocation": build_reallocation(campaign),
        "diagnostics": {
            "corr_spend_romi": corr_spend_romi,
            "corr_spend_orders": corr_spend_orders,
            "banner_impression_share": banner_impressions / total_impressions,
            "banner_impressions": banner_impressions,
            "youtube_profit_share": youtube_profit / total_profit,
            "negative_romi_days": int((daily["romi"] < 0).sum()),
            "best_romi_day": pd.Timestamp(best_day),
            "worst_romi_day": pd.Timestamp(worst_day),
            "peak_spend_day": pd.Timestamp(peak_day),
        },
    }
