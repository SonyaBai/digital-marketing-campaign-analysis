-- Question 3. Funnel rates.
--
-- CTR            = clicks / impressions
-- Click-to-lead  = leads / clicks          (conv1)
-- Lead-to-order  = orders / leads          (conv2)
--
-- Rates are ratios of sums. The banner is about two thirds of impressions
-- and a very low CTR, so the blended CTR is also reported without it.

SELECT
    'all' AS scope,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(leads) AS leads,
    SUM(orders) AS orders,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(leads) / SUM(clicks), 2) AS click_to_lead_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct
FROM campaign_daily

UNION ALL

SELECT
    'excluding_banner' AS scope,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(leads) AS leads,
    SUM(orders) AS orders,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(leads) / SUM(clicks), 2) AS click_to_lead_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct
FROM campaign_daily
WHERE campaign_name <> 'banner_partner';

SELECT
    category,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(leads) / SUM(clicks), 2) AS click_to_lead_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct
FROM campaign_daily
GROUP BY category
ORDER BY category;

SELECT
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(leads) AS leads,
    SUM(orders) AS orders,
    ROUND(100.0 * SUM(clicks) / SUM(impressions), 3) AS ctr_pct,
    ROUND(100.0 * SUM(leads) / SUM(clicks), 2) AS click_to_lead_pct,
    ROUND(100.0 * SUM(orders) / SUM(leads), 2) AS lead_to_order_pct
FROM campaign_daily
GROUP BY campaign_name
ORDER BY campaign_name;
