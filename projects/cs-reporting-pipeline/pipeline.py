"""CS reporting pipeline: raw CRM, support and usage data -> health scores,
renewal watchlist, ticket triage queue, data-quality report and AI-ready QBR inputs.

Run:  pip install duckdb
      python generate_sample_data.py
      python pipeline.py

Design rule: deterministic steps (SQL + rules) produce every number. The LLM step
only writes prose from a small, pre-computed JSON summary, and a person reviews it.
"""
import json
import re
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
DATA, OUT = HERE / "data", HERE / "output"
(OUT / "qbr_inputs").mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
for name in ["accounts", "weekly_usage", "tickets"]:
    con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{DATA / (name + '.csv')}', all_varchar=false)")
con.execute((HERE / "sql" / "mart.sql").read_text())


# ---------- 1. Data-quality checks (run before anyone trusts the numbers) ----------
checks = {
    "Accounts missing a renewal date":
        "SELECT account_id, account_name FROM accounts WHERE renewal_date IS NULL OR CAST(renewal_date AS VARCHAR) = ''",
    "Duplicate account records (same name + owner)":
        "SELECT account_name, csm_owner, LIST(account_id) AS ids FROM accounts GROUP BY 1,2 HAVING COUNT(*) > 1",
    "Tickets linked to an unknown account":
        "SELECT ticket_id, account_id FROM tickets WHERE account_id NOT IN (SELECT account_id FROM accounts)",
    "Accounts with missing usage weeks (expect 12)":
        "SELECT account_id, COUNT(*) AS weeks FROM weekly_usage GROUP BY 1 HAVING COUNT(*) < 12",
}
dq_lines = ["# Data-quality report", "",
            "Issues found in the source data. Each one goes to the system owner to fix at the source, not by hand in a report.", ""]
for title, sql in checks.items():
    rows = con.execute(sql).fetchall()
    dq_lines.append(f"## {title}: {len(rows)}")
    dq_lines += [f"- {r}" for r in rows] or ["- None"]
    dq_lines.append("")
(OUT / "data_quality_report.md").write_text("\n".join(dq_lines))


# ---------- 2. Health scores + renewal watchlist ----------
con.execute(f"COPY (SELECT account_id, account_name, segment, arr_usd, csm_owner, renewal_date, health_score, health_band, "
            f"ROUND(pts_adoption,1) AS pts_adoption, pts_trend, ROUND(pts_integrations,1) AS pts_integrations, pts_support, pts_engagement "
            f"FROM mart_account_health ORDER BY health_score) "
            f"TO '{OUT / 'account_health.csv'}' (HEADER)")
con.execute(f"COPY (SELECT * FROM mart_renewal_watchlist) TO '{OUT / 'renewal_watchlist.csv'}' (HEADER)")


# ---------- 3. Ticket triage: rules first, LLM only for what rules can't place ----------
RULES = [
    ("Identity & SSO", r"\b(sso|okta|login|saml|mfa)\b"),
    ("Integrations", r"\b(connector|integration|api|token|sync)\b"),
    ("Detections & alerts", r"\b(alert|detection|risky|oauth)\b"),
    ("Performance", r"\b(slow|timeout|timing out|loads)\b"),
]
def triage(subject: str) -> str:
    s = subject.lower()
    for queue, pattern in RULES:
        if re.search(pattern, s):
            return queue
    return "Needs review (LLM suggestion + human check)"

open_tickets = con.execute("SELECT ticket_id, account_id, priority, subject FROM tickets WHERE status <> 'solved' ORDER BY priority").fetchall()
triaged = [(t, a, p, s, triage(s)) for t, a, p, s in open_tickets]
con.execute("CREATE TABLE triage (ticket_id VARCHAR, account_id VARCHAR, priority VARCHAR, subject VARCHAR, queue VARCHAR)")
con.executemany("INSERT INTO triage VALUES (?,?,?,?,?)", triaged)
con.execute(f"COPY triage TO '{OUT / 'triage_queue.csv'}' (HEADER)")


# ---------- 4. AI-ready QBR inputs: small, minimized JSON per at-risk account ----------
# Only aggregates leave the warehouse. No user names, emails or raw ticket text.
at_risk = con.execute("""SELECT account_id, account_name, segment, health_score, health_band, days_to_renewal,
                                ROUND(active_rate_recent*100,1), ROUND(active_rate_prior*100,1),
                                integrations_now, target_integrations, open_p1_p2, tickets_30d
                         FROM mart_account_health WHERE health_band = 'At risk' ORDER BY health_score""").fetchall()
for r in at_risk:
    payload = dict(zip(["account_id", "account_name", "segment", "health_score", "health_band", "days_to_renewal",
                        "active_rate_recent_pct", "active_rate_prior_pct", "integrations_now",
                        "target_integrations", "open_p1_p2_tickets", "tickets_last_30_days"], r))
    (OUT / "qbr_inputs" / f"{r[0]}.json").write_text(json.dumps(payload, indent=2, default=str))


# ---------- 5. Executive summary ----------
bands = dict(con.execute("SELECT health_band, COUNT(*) FROM mart_account_health GROUP BY 1").fetchall())
arr_risk = con.execute("SELECT SUM(arr_usd) FROM mart_account_health WHERE health_band = 'At risk'").fetchone()[0] or 0
watch = con.execute("SELECT COUNT(*), SUM(arr_usd) FROM mart_renewal_watchlist").fetchone()
queues = con.execute("SELECT queue, COUNT(*) FROM triage GROUP BY 1 ORDER BY 2 DESC").fetchall()
auto = sum(n for q, n in queues if not q.startswith("Needs review"))
summary = [
    "# CS executive summary (sample data)", "",
    f"- **Accounts scored:** {sum(bands.values())} (Healthy {bands.get('Healthy',0)}, Watch {bands.get('Watch',0)}, At risk {bands.get('At risk',0)})",
    f"- **ARR at risk:** ${arr_risk:,.0f}",
    f"- **Renewals to act on in the next 120 days:** {watch[0]} accounts, ${watch[1] or 0:,.0f} ARR",
    f"- **Open tickets routed automatically by rules:** {auto} of {len(triaged)} ({auto/len(triaged):.0%}); the rest go to LLM suggestion + human review",
    "", "## Triage queues", "", *[f"- {q}: {n}" for q, n in queues],
]
(OUT / "exec_summary.md").write_text("\n".join(summary))
print("\n".join(summary))
print(f"\nOutputs written to {OUT}")
