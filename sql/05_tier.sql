-- Question 5. Tier 1 cities versus tier 2 cities.
--
-- Tier is read from the campaign name. Only the four city campaigns are
-- included: facebook_tier1, facebook_tier2, instagram_tier1, instagram_tier2.
-- The other seven campaigns are not a city tier and are excluded.
-- facebOOK_tier2 in the raw file is facebook_tier2 here.

SELECT
    city_tier,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(leads) AS leads,
    SUM(orders) AS orders,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd
FROM campaign_daily
WHERE city_tier IN ('tier1', 'tier2')
GROUP BY city_tier
ORDER BY city_tier;

SELECT
    platform,
    city_tier,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd
FROM campaign_daily
WHERE city_tier IN ('tier1', 'tier2')
GROUP BY platform, city_tier
ORDER BY platform, city_tier;
