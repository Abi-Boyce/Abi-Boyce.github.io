# Data dictionary

All data in this project is fictional sample data.

## Sources

| Table | Mirrors | Grain | Key fields |
| --- | --- | --- | --- |
| `accounts` | CRM (e.g., Salesforce accounts + renewal opportunities) | One row per account | `account_id`, `segment`, `arr_usd`, `licensed_seats`, `renewal_date`, `csm_owner`, `target_integrations`, `last_csm_touch` |
| `weekly_usage` | Product telemetry | One row per account per week | `weekly_active_users`, `integrations_connected` |
| `tickets` | Support desk (e.g., Zendesk) | One row per ticket | `priority` (P1–P4), `subject`, `status`, `first_response_hours` |

## Mart views (`sql/mart.sql`)

| View | What it answers | Notes |
| --- | --- | --- |
| `dim_account` | One clean row per account | Removes duplicate records (same name + owner), keeping the lowest id |
| `fct_adoption` | Is usage rising or falling? | Active rate = weekly active users / licensed seats; last 4 weeks vs. the 4 before |
| `fct_support` | How heavy is the support load? | Open P1/P2 count, tickets and average first response in the last 30 days |
| `mart_account_health` | How healthy is each account, and why? | Score 0–100 with each component kept as its own column |
| `mart_renewal_watchlist` | Which renewals need action now? | Renewing within 120 days and not Healthy, or adoption falling; includes a next action |

## Health score

| Component | Points | Full points when… |
| --- | --- | --- |
| Adoption | 35 | 70%+ of licensed seats active weekly |
| Adoption trend | 15 | Active rate up 2+ points vs. prior 4 weeks (9 points if flat, 0 if falling) |
| Integration coverage | 20 | Connected integrations reach the account's target |
| Support | 20 | No open P1/P2 tickets (minus 6 points each) |
| Engagement | 10 | CSM contact within 30 days (5 points within 60) |

Bands: **Healthy** 70+, **Watch** 50–69, **At risk** under 50. Weights are a starting point to tune with CSMs against real renewal outcomes.

## Known data-quality checks

Missing renewal dates, duplicate accounts, tickets tied to unknown accounts, and missing usage weeks. See `output/data_quality_report.md`.
