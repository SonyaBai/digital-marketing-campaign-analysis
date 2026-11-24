-- Question 8. A budget reallocation backed by the observed month.
--
-- Pause the four campaigns whose CAC is well above AOV. This case does not
-- assume any campaign can take more budget. It only drops rows that lost money.
--
--   pause   facebook_lal, facebook_tier2, google_wide, instagram_tier2
--   test    facebook_tier1          near breakeven, hold spend flat
--   hold    banner_partner, instagram_blogger
--   scale   youtube_blogger, instagram_tier1, google_hot, facebook_retargeting
--
-- The third query prices one test of the freed spend: 40% YouTube blogger,
-- 30% Instagram tier 1, 20% Google hot, 10% Facebook retargeting. Incremental
-- gross profit multiplies that added spend by the campaign's observed ROMI.
-- Treat it as an upper bound, not a forecast. The weights are a planning
-- choice (retargeting inventory is small; influencer supply is lumpy).

SELECT
    CASE
        WHEN campaign_name IN ('facebook_lal', 'facebook_tier2', 'google_wide', 'instagram_tier2') THEN 'pause'
        WHEN campaign_name = 'facebook_tier1' THEN 'test'
        WHEN campaign_name IN ('banner_partner', 'instagram_blogger') THEN 'hold'
        ELSE 'scale'
    END AS action,
    campaign_name,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY campaign_name
ORDER BY action, romi_pct DESC;

SELECT
    'observed' AS scenario,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily

UNION ALL

SELECT
    'pause_four_lossmakers' AS scenario,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    SUM(orders) AS orders
FROM campaign_daily
WHERE campaign_name NOT IN ('facebook_lal', 'facebook_tier2', 'google_wide', 'instagram_tier2');

WITH campaign AS (
    SELECT
        campaign_name,
        SUM(mark_spent) AS spend,
        SUM(revenue) AS revenue
    FROM campaign_daily
    GROUP BY campaign_name
),
freed AS (
    SELECT SUM(spend) AS freed_spend
    FROM campaign
    WHERE campaign_name IN ('facebook_lal', 'facebook_tier2', 'google_wide', 'instagram_tier2')
),
weights AS (
    SELECT 'youtube_blogger' AS campaign_name, 0.40 AS weight, 1 AS sort_order
    UNION ALL SELECT 'instagram_tier1', 0.30, 2
    UNION ALL SELECT 'google_hot', 0.20, 3
    UNION ALL SELECT 'facebook_retargeting', 0.10, 4
)
SELECT
    w.campaign_name,
    w.weight,
    ROUND(f.freed_spend * w.weight, 2) AS added_spend_usd,
    ROUND(100.0 * (c.revenue - c.spend) / c.spend, 2) AS observed_romi_pct,
    ROUND(
        ROUND(f.freed_spend * w.weight, 2) * (c.revenue - c.spend) / c.spend,
        2
    ) AS incremental_gross_profit_usd
FROM weights AS w
JOIN campaign AS c ON c.campaign_name = w.campaign_name
CROSS JOIN freed AS f
ORDER BY w.sort_order;
