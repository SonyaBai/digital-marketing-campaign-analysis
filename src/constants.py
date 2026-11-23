"""Campaign taxonomy shared by the cleaning, metrics, and charts.

Targeting is not a column in the source file. It is read off the campaign
name and describes how the media was bought:

- retargeting: facebook_retargeting
- lookalike: facebook_lal
- broad: open-audience prospecting (city-tier social, wide-match search, banner)
- high_intent: google_hot, search demand capture, kept out of the broad bucket
- influencer: blogger campaigns, a channel rather than an audience tactic

sql/06_targeting.sql and sql/08_reallocation.sql repeat these names.
"""

from __future__ import annotations

CAMPAIGN_LABELS: dict[str, str] = {
    "youtube_blogger": "YouTube blogger",
    "facebook_retargeting": "Facebook retargeting",
    "google_hot": "Google hot",
    "instagram_tier1": "Instagram tier 1",
    "instagram_blogger": "Instagram blogger",
    "banner_partner": "Banner partner",
    "facebook_tier1": "Facebook tier 1",
    "facebook_tier2": "Facebook tier 2",
    "google_wide": "Google wide",
    "instagram_tier2": "Instagram tier 2",
    "facebook_lal": "Facebook lookalike",
}

CATEGORY_LABELS: dict[str, str] = {
    "influencer": "Influencer",
    "social": "Social",
    "search": "Search",
    "media": "Media",
}

PLATFORM_LABELS: dict[str, str] = {
    "youtube": "YouTube",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "google": "Google",
    "banner": "Banner",
}

TARGETING_LABELS: dict[str, str] = {
    "influencer": "Influencer",
    "retargeting": "Retargeting",
    "high_intent": "High intent",
    "broad": "Broad",
    "lookalike": "Lookalike",
}

TIER_LABELS: dict[str, str] = {
    "tier1": "Tier 1",
    "tier2": "Tier 2",
    "not_tiered": "Not tiered",
}

# Explicit on purpose: an unrecognised campaign should fail, not fall into broad.
PLATFORM_BY_CAMPAIGN: dict[str, str] = {
    "facebook_tier1": "facebook",
    "facebook_tier2": "facebook",
    "facebook_retargeting": "facebook",
    "facebook_lal": "facebook",
    "instagram_tier1": "instagram",
    "instagram_tier2": "instagram",
    "instagram_blogger": "instagram",
    "google_hot": "google",
    "google_wide": "google",
    "youtube_blogger": "youtube",
    "banner_partner": "banner",
}

TIER_BY_CAMPAIGN: dict[str, str] = {
    "facebook_tier1": "tier1",
    "facebook_tier2": "tier2",
    "instagram_tier1": "tier1",
    "instagram_tier2": "tier2",
}

TARGETING_BY_CAMPAIGN: dict[str, str] = {
    "facebook_retargeting": "retargeting",
    "facebook_lal": "lookalike",
    "google_hot": "high_intent",
    "youtube_blogger": "influencer",
    "instagram_blogger": "influencer",
    "facebook_tier1": "broad",
    "facebook_tier2": "broad",
    "instagram_tier1": "broad",
    "instagram_tier2": "broad",
    "google_wide": "broad",
    "banner_partner": "broad",
}

# Campaigns whose February CAC sat above AOV by a wide margin.
# facebook_tier1 is also slightly negative and is handled as a test, not a pause.
PAUSE_CAMPAIGNS: tuple[str, ...] = (
    "facebook_lal",
    "facebook_tier2",
    "google_wide",
    "instagram_tier2",
)

# Near breakeven. Keep the current spend and require a creative test to clear 0% ROMI.
TEST_CAMPAIGNS: tuple[str, ...] = ("facebook_tier1",)

# Profitable, but a weaker use of the next rupee than the scale list.
HOLD_CAMPAIGNS: tuple[str, ...] = (
    "banner_partner",
    "instagram_blogger",
)

# Share of the spend freed by the pause. Weights are a planning choice:
# they respect saturation (retargeting pool, influencer supply), they are not
# an optimised allocation. The last weight absorbs any leftover paisa.
REALLOCATION_WEIGHTS: tuple[tuple[str, str], ...] = (
    ("youtube_blogger", "0.40"),
    ("instagram_tier1", "0.30"),
    ("google_hot", "0.20"),
    ("facebook_retargeting", "0.10"),
)

WEEKDAY_ORDER: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

RAW_COLUMNS: tuple[str, ...] = (
    "id",
    "c_date",
    "campaign_name",
    "category",
    "campaign_id",
    "impressions",
    "mark_spent",
    "clicks",
    "leads",
    "orders",
    "revenue",
)
