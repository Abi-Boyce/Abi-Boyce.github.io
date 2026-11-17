-- CS reporting mart (DuckDB SQL; the same patterns carry over to Databricks SQL).
-- Raw sources are loaded as tables named accounts, weekly_usage and tickets.

-- 1. Clean accounts: one row per account, duplicates removed (keep the lowest id).
CREATE OR REPLACE VIEW dim_account AS
SELECT * EXCLUDE (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY account_name, csm_owner ORDER BY account_id) AS rn
  FROM accounts
) WHERE rn = 1;

-- 2. Adoption: average weekly active rate in the last 4 weeks vs the 4 weeks before.
CREATE OR REPLACE VIEW fct_adoption AS
WITH ranked AS (
  SELECT u.account_id, u.week_start, u.weekly_active_users, u.integrations_connected,
         a.licensed_seats, a.target_integrations,
         DENSE_RANK() OVER (PARTITION BY u.account_id ORDER BY u.week_start DESC) AS wk_back
  FROM weekly_usage u JOIN dim_account a USING (account_id)
)
SELECT account_id,
       AVG(weekly_active_users::DOUBLE / licensed_seats) FILTER (WHERE wk_back <= 4)          AS active_rate_recent,
       AVG(weekly_active_users::DOUBLE / licensed_seats) FILTER (WHERE wk_back BETWEEN 5 AND 8) AS active_rate_prior,
       MAX(integrations_connected) FILTER (WHERE wk_back = 1)                                  AS integrations_now,
       ANY_VALUE(target_integrations)                                                         AS target_integrations
FROM ranked GROUP BY account_id;

-- 3. Support load: open high-priority tickets and response time over the last 30 days.
CREATE OR REPLACE VIEW fct_support AS
SELECT account_id,
       COUNT(*) FILTER (WHERE status <> 'solved' AND priority IN ('P1','P2')) AS open_p1_p2,
       COUNT(*) FILTER (WHERE created_date >= DATE '2026-11-17' - INTERVAL 30 DAY) AS tickets_30d,
       ROUND(AVG(first_response_hours) FILTER (WHERE created_date >= DATE '2026-11-17' - INTERVAL 30 DAY), 1) AS avg_first_response_hrs_30d
FROM tickets GROUP BY account_id;

-- 4. Health score (0-100). Weights are explicit so CSMs can see why a score moved.
--    Adoption 35 | Adoption trend 15 | Integration coverage 20 | Support 20 | Engagement 10
CREATE OR REPLACE VIEW mart_account_health AS
WITH base AS (
  SELECT a.account_id, a.account_name, a.segment, a.arr_usd, a.csm_owner,
         TRY_CAST(a.renewal_date AS DATE) AS renewal_date,
         DATE '2026-11-17' - CAST(a.last_csm_touch AS DATE) AS days_since_touch,
         ad.active_rate_recent, ad.active_rate_prior, ad.integrations_now, ad.target_integrations,
         COALESCE(s.open_p1_p2, 0) AS open_p1_p2, COALESCE(s.tickets_30d, 0) AS tickets_30d,
         s.avg_first_response_hrs_30d
  FROM dim_account a
  LEFT JOIN fct_adoption ad USING (account_id)
  LEFT JOIN fct_support  s  USING (account_id)
), scored AS (
  SELECT *,
    LEAST(active_rate_recent / 0.70, 1) * 35                                              AS pts_adoption,
    CASE WHEN active_rate_recent - active_rate_prior >= 0.02 THEN 15
         WHEN active_rate_recent - active_rate_prior >= -0.02 THEN 9 ELSE 0 END           AS pts_trend,
    LEAST(integrations_now::DOUBLE / target_integrations, 1) * 20                        AS pts_integrations,
    GREATEST(20 - open_p1_p2 * 6, 0)                                                     AS pts_support,
    CASE WHEN days_since_touch <= 30 THEN 10 WHEN days_since_touch <= 60 THEN 5 ELSE 0 END AS pts_engagement
  FROM base
)
SELECT *,
  ROUND(pts_adoption + pts_trend + pts_integrations + pts_support + pts_engagement) AS health_score,
  CASE WHEN ROUND(pts_adoption + pts_trend + pts_integrations + pts_support + pts_engagement) >= 70 THEN 'Healthy'
       WHEN ROUND(pts_adoption + pts_trend + pts_integrations + pts_support + pts_engagement) >= 50 THEN 'Watch'
       ELSE 'At risk' END AS health_band,
  renewal_date - DATE '2026-11-17' AS days_to_renewal
FROM scored;

-- 5. Renewal watchlist: renewing within 120 days and not healthy, or adoption falling.
CREATE OR REPLACE VIEW mart_renewal_watchlist AS
SELECT account_id, account_name, segment, arr_usd, csm_owner, renewal_date, days_to_renewal,
       health_score, health_band,
       ROUND((active_rate_recent - active_rate_prior) * 100, 1) AS adoption_change_pts,
       open_p1_p2,
       CASE WHEN health_band = 'At risk' THEN 'Exec sponsor call + recovery plan this week'
            WHEN open_p1_p2 > 0 THEN 'Clear open P1/P2 tickets with Support before renewal talks'
            WHEN active_rate_recent < active_rate_prior THEN 'Adoption check-in: find teams that stopped using it'
            ELSE 'Schedule renewal QBR' END AS next_action
FROM mart_account_health
WHERE days_to_renewal BETWEEN 0 AND 120
  AND (health_band <> 'Healthy' OR active_rate_recent < active_rate_prior)
ORDER BY days_to_renewal;
