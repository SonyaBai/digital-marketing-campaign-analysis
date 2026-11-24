-- Question 4. Unit economics.
--
-- CPC = mark_spent / clicks
-- CPL = mark_spent / leads
-- CAC = mark_spent / orders
-- AOV = revenue / orders
-- Gross profit = revenue - mark_spent
-- Profit per order = AOV - CAC = gross profit / orders
--
-- A campaign with CAC above AOV loses money on every order it adds,
-- until the rate itself changes.

SELECT
    'portfolio' AS segment,
    ROUND(SUM(mark_spent) / SUM(clicks), 2) AS cpc_usd,
    ROUND(SUM(mark_spent) / SUM(leads), 2) AS cpl_usd,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND((SUM(revenue) - SUM(mark_spent)) / SUM(orders), 2) AS profit_per_order_usd
FROM campaign_daily;

SELECT
    campaign_name,
    ROUND(SUM(mark_spent) / SUM(clicks), 2) AS cpc_usd,
    ROUND(SUM(mark_spent) / SUM(leads), 2) AS cpl_usd,
    ROUND(SUM(mark_spent) / SUM(orders), 2) AS cac_usd,
    ROUND(SUM(revenue) / SUM(orders), 2) AS aov_usd,
    ROUND(SUM(revenue) - SUM(mark_spent), 2) AS gross_profit_usd,
    ROUND((SUM(revenue) - SUM(mark_spent)) / SUM(orders), 2) AS profit_per_order_usd,
    SUM(orders) AS orders
FROM campaign_daily
GROUP BY campaign_name
ORDER BY (SUM(revenue) - SUM(mark_spent)) / SUM(orders) DESC;
