"""Charts for the February 2021 campaign review.

Each figure states the comparison in the title and the reading rule in the
subtitle. Bar labels use the same half-up formatting as the printed tables.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

from src.constants import CAMPAIGN_LABELS, TARGETING_LABELS, WEEKDAY_ORDER
from src.constants import INR_PER_USD
from src.formatters import pretty_label, rate_pct, thousands_float, usd_thousands

INK = "#1C2B33"
TEAL = "#1F7A6B"
CORAL = "#C4493A"
GOLD = "#B5812F"
NAVY = "#1E3A5F"
BLUE = "#3D6F99"
SLATE = "#5C6B73"
SPEND = "#8A8178"
SAND = "#F3E6C8"
GRID = "#E6E0D6"
MUTED = "#C8C2B8"

SOURCE = f"February 2021  ·  USD at {INR_PER_USD} INR per USD  ·  11 campaigns  ·  308 campaign-days"


def _apply_style() -> None:
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#E0DACF",
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 11,
            "axes.titleweight": "regular",
            "axes.labelsize": 10,
            "xtick.color": SLATE,
            "ytick.color": INK,
            "text.color": INK,
            "font.size": 10,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.unicode_minus": False,
            "legend.frameon": False,
            "legend.fontsize": 9,
        }
    )


def _finish(fig: plt.Figure, path: Path) -> None:
    fig.text(0.0, -0.02, SOURCE, ha="left", va="top", fontsize=8, color=SLATE)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.35)
    plt.close(fig)


def _romi_pct(row: pd.Series) -> str:
    return rate_pct(int(row.gross_profit_cents), int(row.spend_cents), 2)


def plot_romi(report: dict) -> plt.Figure:
    campaign = report["campaign"].sort_values("romi", ascending=True)
    overall = report["overall"].iloc[0]
    portfolio = _romi_pct(overall)
    labels = [CAMPAIGN_LABELS[name] for name in campaign.index]
    values = campaign["romi"].to_numpy()
    colors = [TEAL if value >= 0 else CORAL for value in values]

    fig, ax = plt.subplots(figsize=(11.2, 6.6), constrained_layout=True)
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.72, zorder=2)
    ax.axvline(0, color=INK, linewidth=0.8, zorder=3)
    ax.axvline(
        float(overall.romi),
        color=GOLD,
        linestyle="--",
        linewidth=1.15,
        zorder=3,
        label=f"Portfolio {portfolio}",
    )
    span = float(values.max() - values.min())
    pad = span * 0.025
    for ypos, value, row in zip(y, values, campaign.itertuples()):
        label = rate_pct(int(row.gross_profit_cents), int(row.spend_cents), 2)
        if value >= 0:
            ax.text(value + pad, ypos, label, va="center", ha="left", fontsize=8.5, color=INK)
        else:
            ax.text(value - pad, ypos, label, va="center", ha="right", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("ROMI  (revenue − spend) / spend")
    ax.set_xlim(float(values.min()) - span * 0.18, float(values.max()) + span * 0.16)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _pos: f"{v * 100:.0f}%"))
    ax.legend(loc="lower right")
    ax.set_title(
        f"Six campaigns clear their spend. Five do not. The book still returns {portfolio}.",
        loc="left",
        color=SLATE,
        pad=10,
    )
    fig.suptitle("ROMI by campaign", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def plot_funnel(report: dict) -> plt.Figure:
    overall = report["overall"].iloc[0]
    ex_banner = report["ex_banner"].iloc[0]
    stages = ["Impressions", "Clicks", "Leads", "Orders"]
    values = [
        int(overall.impressions),
        int(overall.clicks),
        int(overall.leads),
        int(overall.orders),
    ]
    colors = [NAVY, BLUE, TEAL, GOLD]

    rates = report["category"].copy()
    long = rates.reset_index().melt(
        id_vars="category",
        value_vars=["ctr", "conv1", "conv2"],
        var_name="step",
        value_name="rate",
    )
    long["step"] = long["step"].map(
        {"ctr": "CTR", "conv1": "Click to lead", "conv2": "Lead to order"}
    )
    long["category"] = long["category"].map(pretty_label)
    category_order = [pretty_label(name) for name in report["category"].index]
    step_order = ["CTR", "Click to lead", "Lead to order"]

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 6.3), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.15]})

    ax = axes[0]
    ax.barh(stages, values, color=colors, height=0.66, zorder=2)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(3_000, max(values) * 12)
    ax.set_xlabel("Volume, log scale")
    for stage, value in zip(stages, values):
        ax.text(value * 1.18, stage, f"{value:,.0f}", va="center", ha="left", fontsize=9, color=INK)
    ctr = rate_pct(int(overall.clicks), int(overall.impressions), 3)
    ctr_ex = rate_pct(int(ex_banner.clicks), int(ex_banner.impressions), 3)
    conv1 = rate_pct(int(overall.leads), int(overall.clicks), 2)
    conv2 = rate_pct(int(overall.orders), int(overall.leads), 2)
    ax.set_title(
        f"CTR {ctr} overall, {ctr_ex} without the banner.\nClick to lead {conv1}. Lead to order {conv2}.",
        loc="left",
        color=SLATE,
    )

    ax = axes[1]
    sns.barplot(
        data=long,
        x="category",
        y="rate",
        hue="step",
        order=category_order,
        hue_order=step_order,
        palette=[NAVY, TEAL, GOLD],
        errorbar=None,
        ax=ax,
    )
    ax.set_ylabel("Conversion rate")
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _pos: f"{v * 100:.0f}%"))
    ax.set_ylim(0, float(long["rate"].max()) * 1.32)
    ax.legend(title="", loc="upper right")
    exact = {}
    for key, row in report["category"].iterrows():
        label = pretty_label(key)
        exact[(label, "CTR")] = rate_pct(int(row.clicks), int(row.impressions), 3)
        exact[(label, "Click to lead")] = rate_pct(int(row.leads), int(row.clicks), 2)
        exact[(label, "Lead to order")] = rate_pct(int(row.orders), int(row.leads), 2)
    for step, container in zip(step_order, ax.containers):
        ax.bar_label(
            container,
            labels=[exact[(category, step)] for category in category_order],
            fontsize=7.5,
            padding=2,
            color=INK,
        )
    ax.set_title("The same three rates by category. Media CTR is the short navy bar.", loc="left", color=SLATE)
    fig.suptitle("Funnel", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def plot_spend_revenue(report: dict) -> plt.Figure:
    campaign = report["campaign"].sort_values("spend_cents", ascending=True)
    labels = [CAMPAIGN_LABELS[name] for name in campaign.index]
    y = np.arange(len(labels))
    spend = campaign["spend_cents"].map(thousands_float).to_numpy()
    revenue = campaign["revenue_cents"].map(thousands_float).to_numpy()
    height = 0.38

    fig, ax = plt.subplots(figsize=(11.2, 6.8), constrained_layout=True)
    ax.barh(y + height / 2, spend, height=height, color=SPEND, label="Spend", zorder=2)
    ax.barh(y - height / 2, revenue, height=height, color=TEAL, label="Revenue", zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("USD thousands")
    span = max(float(revenue.max()), float(spend.max()))
    pad = span * 0.012
    ax.set_xlim(0, span * 1.22)
    for ypos, spent, earned in zip(y, spend, revenue):
        ax.text(spent + pad, ypos + height / 2, f"{spent:.2f}", va="center", ha="left", fontsize=7.5, color=SLATE)
        ax.text(earned + pad, ypos - height / 2, f"{earned:.2f}", va="center", ha="left", fontsize=7.5, color=TEAL)
    ax.legend(loc="lower right")
    ax.set_title(
        "Where the teal bar is shorter than the gray bar, the campaign lost money.",
        loc="left",
        color=SLATE,
        pad=10,
    )
    fig.suptitle("Spend and revenue by campaign", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def plot_tier(report: dict) -> plt.Figure:
    tier = report["tier"].reset_index().rename(columns={"city_tier": "tier"})
    tier_long = tier.melt(id_vars="tier", value_vars=["spend_cents", "revenue_cents"], var_name="metric", value_name="cents")
    tier_long["USD thousands"] = tier_long["cents"].map(thousands_float)
    tier_long["tier"] = tier_long["tier"].map(pretty_label)
    tier_long["metric"] = tier_long["metric"].map({"spend_cents": "Spend", "revenue_cents": "Revenue"})

    cells = report["tier_platform"].reset_index()
    tier_name = {"tier1": "tier 1", "tier2": "tier 2"}
    cells["label"] = cells["platform"].map(pretty_label) + " " + cells["city_tier"].map(tier_name)
    cells = cells.sort_values("romi", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 6.2), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.15]})

    ax = axes[0]
    sns.barplot(
        data=tier_long,
        x="tier",
        y="USD thousands",
        hue="metric",
        order=["Tier 1", "Tier 2"],
        hue_order=["Spend", "Revenue"],
        palette=[SPEND, TEAL],
        errorbar=None,
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("USD thousands")
    ax.legend(title="", loc="upper right")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", fontsize=8.5, padding=2, color=INK)
    ax.set_ylim(0, float(tier_long["USD thousands"].max()) * 1.2)
    tier1 = report["tier"].loc["tier1"]
    tier2 = report["tier"].loc["tier2"]
    ax.set_title(
        f"Tier 1 ROMI {_romi_pct(tier1)} on lead-to-order {rate_pct(int(tier1.orders), int(tier1.leads), 2)}.\n"
        f"Tier 2 ROMI {_romi_pct(tier2)} on lead-to-order {rate_pct(int(tier2.orders), int(tier2.leads), 2)}.",
        loc="left",
        color=SLATE,
    )

    ax = axes[1]
    colors = [TEAL if value >= 0 else CORAL for value in cells["romi"]]
    ax.barh(cells["label"], cells["romi"], color=colors, height=0.68, zorder=2)
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.invert_yaxis()
    for ypos, row in enumerate(cells.itertuples()):
        label = rate_pct(int(row.gross_profit_cents), int(row.spend_cents), 2)
        offset = 0.04 if row.romi >= 0 else -0.04
        align = "left" if row.romi >= 0 else "right"
        ax.text(row.romi + offset, ypos, label, va="center", ha=align, fontsize=9, color=INK)
    ax.set_xlabel("ROMI")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _pos: f"{v * 100:.0f}%"))
    ax.set_xlim(-0.7, 1.15)
    ax.set_title("Instagram tier 1 carries the city split.\nBoth Facebook city tiers lose money.", loc="left", color=SLATE)
    fig.suptitle("Tier 1 and tier 2 cities", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def plot_targeting(report: dict) -> plt.Figure:
    order = ["influencer", "retargeting", "high_intent", "broad", "lookalike"]
    frame = report["targeting"].reindex(order)
    labels = [TARGETING_LABELS[name] for name in frame.index]
    values = frame["romi"].to_numpy()
    # Influencer and high intent are context, not the three-way comparison.
    colors = []
    for name, value in zip(frame.index, values):
        if name in {"influencer", "high_intent"}:
            colors.append(MUTED if value >= 0 else CORAL)
        else:
            colors.append(TEAL if value >= 0 else CORAL)

    fig, ax = plt.subplots(figsize=(11.2, 6.2), constrained_layout=True)
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.68, zorder=2)
    ax.axvline(0, color=INK, linewidth=0.8, zorder=3)
    ax.invert_yaxis()
    for ypos, name, row in zip(y, frame.index, frame.itertuples()):
        label = (
            f"{rate_pct(int(row.gross_profit_cents), int(row.spend_cents), 2)}"
            f"   ·   {usd_thousands(int(row.spend_cents))} spend"
        )
        # Negative bars would push a left-hand label into the category names.
        # Park that label in the empty space to the right of zero instead.
        anchor = row.romi + 0.06 if row.romi >= 0 else 0.08
        ax.text(anchor, ypos, label, va="center", ha="left", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("ROMI")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _pos: f"{v * 100:.0f}%"))
    ax.set_xlim(-1.15, 3.15)
    ax.legend(
        handles=[
            Patch(facecolor=TEAL, label="Profitable, in the comparison"),
            Patch(facecolor=CORAL, label="Loss"),
            Patch(facecolor=MUTED, label="Context, not part of broad"),
        ],
        loc="lower right",
        bbox_to_anchor=(1.0, 0.18),
    )
    ax.set_title(
        "Broad is city-tier social, wide-match search, and the banner. High-intent search is separate.",
        loc="left",
        color=SLATE,
        pad=10,
    )
    fig.suptitle("Retargeting, lookalike, and broad targeting", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def plot_daily(report: dict) -> plt.Figure:
    daily = report["daily"]
    dates = pd.to_datetime(daily.index)
    spend = daily["spend_cents"].map(thousands_float)
    revenue = daily["revenue_cents"].map(thousands_float)
    romi = daily["romi"] * 100

    fig, ax = plt.subplots(figsize=(12.4, 6.4), constrained_layout=True)
    labeled_weekend = False
    for day, flag in zip(dates, daily["is_weekend"].astype(int)):
        if flag == 1:
            ax.axvspan(
                day - pd.Timedelta(hours=12),
                day + pd.Timedelta(hours=12),
                color=SAND,
                zorder=0,
                label="Weekend" if not labeled_weekend else None,
            )
            labeled_weekend = True
    ax.fill_between(dates, spend, revenue, color=TEAL, alpha=0.16, zorder=1, label="Gross profit")
    ax.plot(dates, spend, color=SPEND, linewidth=2.0, marker="o", markersize=3.5, label="Spend", zorder=3)
    ax.plot(dates, revenue, color=TEAL, linewidth=2.0, marker="o", markersize=3.5, label="Revenue", zorder=3)
    ax.set_ylabel("USD thousands")
    ax.set_xlabel("")

    twin = ax.twinx()
    twin.plot(dates, romi, color=GOLD, linewidth=1.4, linestyle="--", label="ROMI", zorder=4)
    twin.set_ylabel("ROMI", color=GOLD)
    twin.tick_params(axis="y", colors=GOLD)
    twin.spines["right"].set_visible(True)
    twin.spines["right"].set_color("#E0DACF")
    twin.grid(False)
    twin.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _pos: f"{v:.0f}%"))
    twin.set_ylim(0, max(110, float(romi.max()) + 15))

    ax.set_xlim(dates.min() - pd.Timedelta(hours=12), dates.max() + pd.Timedelta(hours=12))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(plt.matplotlib.dates.DayLocator(interval=2))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    handles_left, labels_left = ax.get_legend_handles_labels()
    handles_right, labels_right = twin.get_legend_handles_labels()
    ax.legend(handles_left + handles_right, labels_left + labels_right, loc="upper left", ncol=2)
    peak = report["diagnostics"]["peak_spend_day"].strftime("%-d %b")
    ax.set_title(
        f"ROMI was positive on all 28 days. Spend peaked on {peak}, then was cut.",
        loc="left",
        color=SLATE,
        pad=10,
    )
    fig.suptitle("Daily spend, revenue, and ROMI", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def plot_weekday(report: dict) -> plt.Figure:
    weekday = report["weekday"].reindex(WEEKDAY_ORDER)
    weekend = report["weekend"]
    colors = [GOLD if day in {"Saturday", "Sunday"} else NAVY for day in WEEKDAY_ORDER]
    romi = weekday["romi"].to_numpy() * 100
    profit = weekday["gross_profit_cents"].map(thousands_float).to_numpy()

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 6.0), constrained_layout=True)
    x = np.arange(len(WEEKDAY_ORDER))

    ax = axes[0]
    ax.bar(x, romi, color=colors, width=0.72, zorder=2)
    ax.axhline(float(weekend.loc["Weekday", "romi"]) * 100, color=NAVY, linestyle="--", linewidth=1, label="Weekday average")
    ax.axhline(float(weekend.loc["Weekend", "romi"]) * 100, color=GOLD, linestyle="--", linewidth=1, label="Weekend average")
    ax.set_xticks(x)
    ax.set_xticklabels([day[:3] for day in WEEKDAY_ORDER])
    ax.set_ylabel("ROMI")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _pos: f"{v:.0f}%"))
    for xpos, value, row in zip(x, romi, weekday.itertuples()):
        ax.text(xpos, value + 1.2, rate_pct(int(row.gross_profit_cents), int(row.spend_cents), 2), ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_ylim(0, max(romi) * 1.22)
    ax.legend(loc="upper left")
    wd = _romi_pct(weekend.loc["Weekday"])
    we = _romi_pct(weekend.loc["Weekend"])
    ax.set_title(f"Weekend {we} versus weekday {wd}.", loc="left", color=SLATE)

    ax = axes[1]
    ax.bar(x, profit, color=colors, width=0.72, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([day[:3] for day in WEEKDAY_ORDER])
    ax.set_ylabel("Gross profit, USD thousands")
    lift = max(profit) * 0.025
    for xpos, value in zip(x, profit):
        ax.text(xpos, value + lift, f"{value:.2f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_ylim(0, max(profit) * 1.22)
    ax.legend(handles=[Patch(facecolor=NAVY, label="Weekday"), Patch(facecolor=GOLD, label="Weekend")], loc="upper left")
    ax.set_title("Friday produces the most profit. Sunday does not behave like Saturday.", loc="left", color=SLATE)

    fig.suptitle("Weekday and weekend", fontsize=16, fontweight="bold", color=INK, x=0.0, ha="left")
    return fig


def render_all(report: dict, image_dir: Path) -> list[Path]:
    _apply_style()
    image_dir.mkdir(parents=True, exist_ok=True)
    figures = [
        ("romi_by_campaign.png", plot_romi),
        ("funnel.png", plot_funnel),
        ("spend_vs_revenue.png", plot_spend_revenue),
        ("tier_comparison.png", plot_tier),
        ("targeting_comparison.png", plot_targeting),
        ("daily_trend.png", plot_daily),
        ("weekday_vs_weekend.png", plot_weekday),
    ]
    paths = []
    for name, builder in figures:
        fig = builder(report)
        path = image_dir / name
        _finish(fig, path)
        paths.append(path)
    return paths
