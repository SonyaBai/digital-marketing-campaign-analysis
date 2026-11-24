-- Cleaned daily marketing performance for February 2021.
-- Source file: data/raw/Marketing.csv
-- (Kaggle, "Analyze the Marketing Spending", sinderpreet, CC0).
--
-- Money is US dollars. Each campaign-day in the raw file (INR) is divided by
-- 72.8053, the Federal Reserve G.5 monthly average for February 2021
-- (rupees per dollar), and rounded half-up to the cent.
-- https://www.federalreserve.gov/releases/g5/20210301/
-- gross_profit = revenue - mark_spent. The extract has no
-- product cost, so this is profit after media spend only.
-- campaign_name is lowercased. campaign_name_raw keeps the source text
-- (the only defect is facebOOK_tier2 on campaign_id 348934).
-- platform, city_tier, targeting, weekday, and is_weekend are derived at load.

DROP TABLE IF EXISTS campaign_daily;

CREATE TABLE campaign_daily (
    id INTEGER PRIMARY KEY,
    c_date TEXT NOT NULL CHECK (c_date GLOB '????-??-??'),
    campaign_name TEXT NOT NULL CHECK (campaign_name = lower(campaign_name)),
    campaign_name_raw TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('social', 'search', 'influencer', 'media')),
    campaign_id INTEGER NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('facebook', 'instagram', 'google', 'youtube', 'banner')),
    city_tier TEXT NOT NULL CHECK (city_tier IN ('tier1', 'tier2', 'not_tiered')),
    targeting TEXT NOT NULL CHECK (targeting IN ('retargeting', 'lookalike', 'broad', 'high_intent', 'influencer')),
    impressions INTEGER NOT NULL CHECK (impressions > 0),
    mark_spent REAL NOT NULL CHECK (mark_spent > 0),
    clicks INTEGER NOT NULL CHECK (clicks >= 0 AND clicks <= impressions),
    leads INTEGER NOT NULL CHECK (leads >= 0 AND leads <= clicks),
    orders INTEGER NOT NULL CHECK (orders >= 0 AND orders <= leads),
    revenue REAL NOT NULL CHECK (revenue >= 0),
    gross_profit REAL NOT NULL,
    weekday TEXT NOT NULL CHECK (
        weekday IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    ),
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1)),
    UNIQUE (c_date, campaign_name)
);

CREATE INDEX idx_campaign_daily_date ON campaign_daily (c_date);
CREATE INDEX idx_campaign_daily_category ON campaign_daily (category);
CREATE INDEX idx_campaign_daily_targeting ON campaign_daily (targeting);
CREATE INDEX idx_campaign_daily_tier ON campaign_daily (city_tier);
