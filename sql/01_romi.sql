-- Question 1. Return on marketing investment, overall and by campaign.
--
-- Money columns are US dollars. Each raw campaign-day (INR) was divided by
-- 72.8053, the Federal Reserve G.5 average for February 2021, and rounded
-- half-up to the cent before loading. ROMI is unchanged by that constant rate.
--
-- ROMI = (revenue - mark_spent) / mark_spent.
-- romi_pct is that ratio times 100.
-- Gross profit = revenue - mark_spent. The extract has no product cost.

SELECT
    'portfolio' AS segment,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily;

SELECT
    campaign_name,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd
FROM campaign_daily
GROUP BY campaign_name
ORDER BY (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent) DESC;
