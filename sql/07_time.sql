-- Question 7. Time patterns, including weekday versus weekend.
--
-- is_weekend is 1 for Saturday and Sunday. February 2021 starts on Monday
-- and has four of each weekday, so the weekday totals are comparable
-- without a per-day normalisation. spend_per_day_usd is still shown.
-- Every campaign ran on every date, so a day is 11 campaign-rows.

SELECT
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(DISTINCT c_date) AS days,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(mark_spent) / COUNT(DISTINCT c_date), 2) AS spend_per_day_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND((SUM(revenue) - SUM(mark_spent)) / COUNT(DISTINCT c_date), 2) AS gross_profit_per_day_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY is_weekend
ORDER BY is_weekend;

SELECT
    weekday,
    COUNT(DISTINCT c_date) AS days,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY weekday
ORDER BY CASE weekday
    WHEN 'Monday' THEN 1
    WHEN 'Tuesday' THEN 2
    WHEN 'Wednesday' THEN 3
    WHEN 'Thursday' THEN 4
    WHEN 'Friday' THEN 5
    WHEN 'Saturday' THEN 6
    WHEN 'Sunday' THEN 7
END;

SELECT
    CASE
        WHEN CAST(strftime('%d', c_date) AS INTEGER) <= 14 THEN 'Feb 1-14'
        ELSE 'Feb 15-28'
    END AS half,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY half
ORDER BY half;

SELECT
    c_date,
    is_weekend,
    weekday,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY c_date, is_weekend, weekday
ORDER BY c_date;
