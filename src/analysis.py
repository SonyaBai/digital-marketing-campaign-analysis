"""Regenerate the cleaned extract, the KPI tables, and the charts.

Run from the repository root:

    python analysis.py
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cleaning import clean_marketing, describe_cleaning, export_frame, load_raw
from src.constants import CAMPAIGN_LABELS, PAUSE_CAMPAIGNS
from src.formatters import format_kpi_table, inr, inr_per, rate_pct
from src.metrics import build_report

RAW_PATH = ROOT / "data" / "raw" / "Marketing.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "marketing_clean.csv"
IMAGE_DIR = ROOT / "images"
DB_PATH = ROOT / "data" / "marketing.db"
SQL_DIR = ROOT / "sql"

# Paise totals of the published extract. A mismatch means the raw file changed.
EXPECTED_SPEND_PAISE = 3_059_087_982
EXPECTED_REVENUE_PAISE = 4_288_936_600


def _inr_decimal(amount: Decimal) -> str:
    rounded = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if rounded < 0 else ""
    return f"{sign}₹{abs(rounded):,.2f}"


def _print_table(title: str, frame) -> None:
    print(f"\n{title}")
    print(format_kpi_table(frame).to_string(index=False))


def print_summary(clean, cleaning: dict, report: dict) -> None:
    overall = report["overall"].iloc[0]
    ex_banner = report["ex_banner"].iloc[0]
    diagnostics = report["diagnostics"]
    plan = report["reallocation"]

    print("CLEANING")
    print(f"Rows                         {cleaning['rows']}")
    print(f"Blank cells                  {cleaning['blank_cells']}")
    print(f"Names with surrounding space {cleaning['whitespace_name_rows']}")
    print(f"Names normalised by case     {cleaning['normalized_name_rows']}  {cleaning['normalized_names']}")
    print("Fix                          lowercase campaign_name; keep campaign_name_raw")
    print("Derived                      platform, city_tier, targeting, weekday, is_weekend, gross_profit")

    print("\nPORTFOLIO")
    print(f"Spend                        {inr(overall.spend_paise)}")
    print(f"Revenue                      {inr(overall.revenue_paise)}")
    print(f"Gross profit                 {inr(overall.gross_profit_paise)}")
    print(f"ROMI                         {rate_pct(overall.gross_profit_paise, overall.spend_paise, 2)}")
    print(f"Orders                       {int(overall.orders):,}")
    print(f"Leads                        {int(overall.leads):,}")
    print(f"Clicks                       {int(overall.clicks):,}")
    print(f"Impressions                  {int(overall.impressions):,}")
    print(f"CTR                          {rate_pct(overall.clicks, overall.impressions, 3)}")
    print(f"CTR excluding banner         {rate_pct(ex_banner.clicks, ex_banner.impressions, 3)}")
    print(f"Click-to-lead excluding banner {rate_pct(ex_banner.leads, ex_banner.clicks, 2)}")
    print(f"Lead-to-order excluding banner {rate_pct(ex_banner.orders, ex_banner.leads, 2)}")
    print(f"Click-to-lead                {rate_pct(overall.leads, overall.clicks, 2)}")
    print(f"Lead-to-order                {rate_pct(overall.orders, overall.leads, 2)}")
    print(f"CPC                          {inr_per(overall.spend_paise, overall.clicks)}")
    print(f"CPL                          {inr_per(overall.spend_paise, overall.leads)}")
    print(f"CAC                          {inr_per(overall.spend_paise, overall.orders)}")
    print(f"AOV                          {inr_per(overall.revenue_paise, overall.orders)}")
    cpm_paise = (Decimal(int(overall.spend_paise)) / Decimal(int(overall.impressions)) * Decimal(1000)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    print(f"CPM                          {inr(int(cpm_paise))}")

    _print_table("BY CAMPAIGN", report["campaign"])
    _print_table("BY CATEGORY", report["category"])
    _print_table("BY PLATFORM", report["platform"])
    _print_table("BY TIER (tiered campaigns only)", report["tier"])
    _print_table("BY PLATFORM AND TIER", report["tier_platform"])
    _print_table("BY TARGETING", report["targeting"])
    _print_table("WEEKDAY VS WEEKEND", report["weekend"])
    _print_table("BY WEEKDAY", report["weekday"])
    _print_table("BY HALF MONTH", report["half"])

    banner_share = rate_pct(diagnostics["banner_impressions"], int(overall.impressions), 2)
    youtube_share = rate_pct(
        int(report["campaign"].loc["youtube_blogger", "gross_profit_paise"]),
        int(overall.gross_profit_paise),
        2,
    )
    print("\nDIAGNOSTICS")
    retarget_impr = int(clean.loc[clean["campaign_name"] == "facebook_retargeting", "impressions"].sum())
    print(f"Banner share of impressions  {banner_share}")
    print(f"Retargeting impressions      {retarget_impr:,}")
    youtube = report["campaign"].loc["youtube_blogger"]
    print(f"YouTube share of spend       {rate_pct(youtube.spend_paise, overall.spend_paise, 2)}")
    print(f"YouTube share of revenue     {rate_pct(youtube.revenue_paise, overall.revenue_paise, 2)}")
    print(f"YouTube share of gross profit {youtube_share}")
    influencer_profit = int(report["category"].loc["influencer", "gross_profit_paise"])
    print(f"Influencer gross profit      {inr(influencer_profit)}")
    print(f"All other categories         {inr(int(overall.gross_profit_paise) - influencer_profit)}")
    print("Profit per order (gross profit / orders)")
    for name, row in report["campaign"].iterrows():
        print(f"  {CAMPAIGN_LABELS[name]:<24} {inr_per(row.gross_profit_paise, row.orders)}")
    for label, row in report["weekend"].iterrows():
        spend_per_day = int((Decimal(int(row.spend_paise)) / Decimal(int(row.days))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        profit_per_day = int(
            (Decimal(int(row.gross_profit_paise)) / Decimal(int(row.days))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        print(
            f"{label} per day               spend {inr(spend_per_day)}  "
            f"gross profit {inr(profit_per_day)}  over {int(row.days)} days"
        )
    print(f"Days with negative ROMI      {diagnostics['negative_romi_days']}")
    print(f"Correlation, daily spend and ROMI    {diagnostics['corr_spend_romi']:.2f}")
    print(f"Correlation, daily spend and orders  {diagnostics['corr_spend_orders']:.2f}")
    best = diagnostics["best_romi_day"]
    worst = diagnostics["worst_romi_day"]
    peak = diagnostics["peak_spend_day"]
    daily = report["daily"]
    print(
        f"Best ROMI day                {best.date()}  "
        f"{rate_pct(daily.loc[best, 'gross_profit_paise'], daily.loc[best, 'spend_paise'], 2)}  "
        f"spend {inr(daily.loc[best, 'spend_paise'])}"
    )
    print(
        f"Worst ROMI day               {worst.date()}  "
        f"{rate_pct(daily.loc[worst, 'gross_profit_paise'], daily.loc[worst, 'spend_paise'], 2)}  "
        f"spend {inr(daily.loc[worst, 'spend_paise'])}"
    )
    print(
        f"Peak spend day               {peak.date()}  "
        f"spend {inr(daily.loc[peak, 'spend_paise'])}  "
        f"revenue {inr(daily.loc[peak, 'revenue_paise'])}  "
        f"ROMI {rate_pct(daily.loc[peak, 'gross_profit_paise'], daily.loc[peak, 'spend_paise'], 2)}  "
        f"orders {int(daily.loc[peak, 'orders']):,}"
    )

    print("\nREALLOCATION")
    print("Pause                        " + ", ".join(CAMPAIGN_LABELS[name] for name in PAUSE_CAMPAIGNS))
    print(f"Freed spend                  {inr(plan['freed_spend_paise'])}")
    print(f"Freed spend share            {rate_pct(plan['freed_spend_paise'], overall.spend_paise, 2)}")
    print(f"Revenue given up             {inr(plan['forgone_revenue_paise'])}")
    print(f"Orders given up              {plan['forgone_orders']:,}")
    print(f"Gross profit of paused lines {inr(plan['forgone_profit_paise'])}")
    print("Pause only, remaining book")
    print(f"  Spend                      {inr(plan['pause_only_spend_paise'])}")
    print(f"  Revenue                    {inr(plan['pause_only_revenue_paise'])}")
    print(f"  Gross profit               {inr(plan['pause_only_profit_paise'])}")
    print(f"  ROMI                       {rate_pct(plan['pause_only_profit_paise'], plan['pause_only_spend_paise'], 2)}")
    print(f"  Orders                     {plan['pause_only_orders']:,}")
    print("Constant-ROMI upper bound if the freed spend is reallocated")
    for row in plan["allocations"]:
        print(
            f"  {CAMPAIGN_LABELS[row['campaign']]:<24} "
            f"weight {row['weight']}  "
            f"add {inr(row['added_spend_paise'])}  "
            f"ROMI {rate_pct(int(report['campaign'].loc[row['campaign'], 'gross_profit_paise']), int(report['campaign'].loc[row['campaign'], 'spend_paise']), 2)}  "
            f"incremental profit {_inr_decimal(row['incremental_gross_profit'])}  "
            f"projected orders {row['projected_orders']:,.2f}"
        )
    print(f"  Incremental gross profit   {_inr_decimal(plan['incremental_gross_profit'])}")
    full_profit = Decimal(plan["pause_only_profit_paise"]) / Decimal(100) + plan["incremental_gross_profit"]
    print(f"  Full-book gross profit     {_inr_decimal(full_profit)}")
    full_spend = Decimal(EXPECTED_SPEND_PAISE) / Decimal(100)
    full_romi = full_profit / full_spend * Decimal(100)
    print(f"  Full-book ROMI             {full_romi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%")
    print(f"  Full-book spend            {_inr_decimal(full_spend)}")


def _check_report(clean, report: dict) -> None:
    overall = report["overall"].iloc[0]
    if int(overall.spend_paise) != EXPECTED_SPEND_PAISE:
        raise AssertionError(f"Spend paise {overall.spend_paise} != {EXPECTED_SPEND_PAISE}")
    if int(overall.revenue_paise) != EXPECTED_REVENUE_PAISE:
        raise AssertionError(f"Revenue paise {overall.revenue_paise} != {EXPECTED_REVENUE_PAISE}")
    if int(clean["gross_profit_paise"].sum()) != EXPECTED_REVENUE_PAISE - EXPECTED_SPEND_PAISE:
        raise AssertionError("Gross profit does not equal revenue minus spend.")
    for name in PAUSE_CAMPAIGNS:
        if int(report["campaign"].loc[name, "gross_profit_paise"]) >= 0:
            raise AssertionError(f"{name} is on the pause list but did not lose money.")
    banner_clicks = int(clean.loc[clean["campaign_name"] == "banner_partner", "clicks"].sum())
    other_clicks = int(clean.loc[clean["campaign_name"] != "banner_partner", "clicks"].sum())
    if banner_clicks + other_clicks != int(overall.clicks):
        raise AssertionError("Banner split does not add up to total clicks.")


def _sql_statements(path: Path) -> list[str]:
    lines = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or stripped == "":
            continue
        lines.append(line)
    return [part.strip() for part in "\n".join(lines).split(";") if part.strip()]


def _verify_sql(report: dict) -> None:
    connection = sqlite3.connect(DB_PATH)
    try:
        mismatch = connection.execute(
            """
            SELECT COUNT(*) FROM campaign_daily
            WHERE is_weekend != CASE
                WHEN strftime('%w', c_date) IN ('0', '6') THEN 1 ELSE 0
            END
            """
        ).fetchone()[0]
        if mismatch:
            raise AssertionError("Stored weekend flag disagrees with the date.")

        portfolio = connection.execute(
            """
            SELECT ROUND(SUM(mark_spent), 2),
                   ROUND(SUM(revenue), 2),
                   ROUND(SUM(revenue) - SUM(mark_spent), 2),
                   COUNT(*)
            FROM campaign_daily
            """
        ).fetchone()
        if abs(portfolio[0] - 30590879.82) > 0.001:
            raise AssertionError(f"SQLite spend {portfolio[0]}")
        if abs(portfolio[1] - 42889366.00) > 0.001:
            raise AssertionError(f"SQLite revenue {portfolio[1]}")
        if abs(portfolio[2] - 12298486.18) > 0.001:
            raise AssertionError(f"SQLite gross profit {portfolio[2]}")
        if portfolio[3] != 308:
            raise AssertionError(f"SQLite row count {portfolio[3]}")

        for path in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
            for statement in _sql_statements(path):
                cursor = connection.execute(statement)
                if cursor.description:
                    cursor.fetchall()

        sql_campaigns = dict(
            connection.execute(
                """
                SELECT campaign_name,
                       ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2)
                FROM campaign_daily
                GROUP BY campaign_name
                """
            ).fetchall()
        )
        for name, row in report["campaign"].iterrows():
            python_romi = rate_pct(int(row.gross_profit_paise), int(row.spend_paise), 2).rstrip("%")
            if abs(float(sql_campaigns[name]) - float(python_romi)) > 0.001:
                raise AssertionError(
                    f"ROMI mismatch for {name}: SQL {sql_campaigns[name]} Python {python_romi}"
                )
    finally:
        connection.close()
    print("\nSQL check                        passed (8 query files, totals and campaign ROMI match)")


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    from src.charts import render_all

    raw = load_raw(RAW_PATH)
    cleaning = describe_cleaning(raw)
    clean = clean_marketing(raw)
    _check_report(clean, build_report(clean))

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    export_frame(clean).to_csv(PROCESSED_PATH, index=False)

    report = build_report(clean)
    _check_report(clean, report)
    written = render_all(report, IMAGE_DIR)
    print_summary(clean, cleaning, report)
    print("\nCHARTS")
    for path in written:
        print(f"  {path.relative_to(ROOT)}")

    sys.stdout.flush()
    subprocess.check_call([sys.executable, str(SQL_DIR / "load_sqlite.py")])
    _verify_sql(report)


if __name__ == "__main__":
    main()
