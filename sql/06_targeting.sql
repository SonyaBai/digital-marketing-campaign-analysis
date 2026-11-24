-- Question 6. Retargeting and lookalike versus broad targeting.
--
-- targeting is derived from the campaign name at load:
--   retargeting   facebook_retargeting
--   lookalike     facebook_lal
--   broad         facebook_tier1, facebook_tier2, instagram_tier1,
--                 instagram_tier2, google_wide, banner_partner
--   high_intent   google_hot          (search demand capture, not broad)
--   influencer    youtube_blogger, instagram_blogger
--
-- High intent and influencer are returned for context. They are not part of
-- the broad bucket. The second query is the three-way comparison.

SELECT
    targeting,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(leads) / SUM(clicks), 2) AS click_to_lead_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct,
    ROUND(SUM(mark_spent) / SUM(clicks), 2) AS cpc_usd,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY targeting
ORDER BY (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent) DESC;

SELECT
    targeting,
    ROUND(SUM(mark_spent), 2) AS spend_usd,
    ROUND(SUM(revenue), 2) AS revenue_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND(100.0 * (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent), 2) AS romi_pct,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct
FROM campaign_daily
WHERE targeting IN ('retargeting', 'lookalike', 'broad')
GROUP BY targeting
ORDER BY (SUM(revenue) - SUM(mark_spent)) / SUM(mark_spent) DESC;
