-- Question 2. Performance by category.
--
-- Categories are the source field: social, search, influencer, media.
-- Social losing money is a mix result. The platform cut below shows that
-- YouTube and Instagram are not the problem, and Facebook is not uniformly bad.

SELECT
    category,
    ROUND(SUM(mark_spent), 2) AS spend_inr,
    ROUND(SUM(revenue), 2) AS revenue_inr,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_inr,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(leads) / SUM(clicks), 2) AS click_to_lead_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_inr,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_inr
FROM campaign_daily
GROUP BY category
ORDER BY (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent) DESC;

SELECT
    platform,
    ROUND(SUM(mark_spent), 2) AS spend_inr,
    ROUND(SUM(revenue), 2) AS revenue_inr,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_inr,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY platform
ORDER BY (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent) DESC;
