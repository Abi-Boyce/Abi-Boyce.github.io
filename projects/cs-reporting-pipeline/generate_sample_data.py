"""Generate fictional sample data for the CS reporting pipeline.

Every company, person and ticket here is invented. The shapes mirror what a
Customer Success team typically pulls from a CRM (accounts and renewals), a
support desk (tickets) and product telemetry (weekly usage).

A few problems are planted on purpose (a missing renewal date, a duplicate
account, an orphan ticket, missing usage weeks) so the data-quality checks
have something real to catch.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(17)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)
TODAY = date(2026, 11, 17)

PREFIX = ["North", "Blue", "Granite", "Summit", "Harbor", "Cedar", "Atlas", "Lumen",
          "Pioneer", "Redwood", "Silver", "Beacon", "Keystone", "Meridian", "Orchard",
          "Prairie", "Quartz", "Riverbend", "Sterling", "Tidewater"]
SUFFIX = ["Health", "Logistics", "Bank", "Retail", "Energy", "Media"]
CSMS = ["CSM A", "CSM B", "CSM C", "CSM D"]
SEGMENTS = [("Enterprise", 180_000, 600_000, 2000), ("Mid-Market", 60_000, 180_000, 600),
            ("Commercial", 25_000, 60_000, 150)]

accounts = []
for i in range(40):
    seg, lo, hi, seats = random.choice(SEGMENTS)
    renewal = TODAY + timedelta(days=random.randint(10, 360))
    accounts.append({
        "account_id": f"ACC-{1001 + i}",
        "account_name": f"{PREFIX[i % 20]} {SUFFIX[i % 6]}",
        "segment": seg,
        "arr_usd": round(random.uniform(lo, hi), -3),
        "licensed_seats": int(seats * random.uniform(0.6, 1.4)),
        "renewal_date": renewal.isoformat(),
        "csm_owner": random.choice(CSMS),
        "target_integrations": random.choice([8, 10, 12, 15]),
        "last_csm_touch": (TODAY - timedelta(days=random.randint(3, 120))).isoformat(),
    })
# Planted data-quality issues
accounts[7]["renewal_date"] = ""                      # missing renewal date
dup = dict(accounts[3]); dup["account_id"] = "ACC-1099"  # duplicate account record
accounts.append(dup)

with open(OUT / "accounts.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(accounts[0].keys()))
    w.writeheader(); w.writerows(accounts)

# Weekly usage: 12 weeks per account. Each account gets a trend so some rise, some fall.
usage = []
for a in accounts[:40]:
    base = random.uniform(0.25, 0.85)
    trend = random.uniform(-0.03, 0.025)
    integ = random.randint(2, a["target_integrations"])
    for wk in range(12):
        if a["account_id"] == "ACC-1022" and wk in (5, 6):
            continue  # planted: missing usage weeks
        week_start = TODAY - timedelta(weeks=12 - wk)
        rate = max(0.03, min(0.98, base + trend * wk + random.uniform(-0.04, 0.04)))
        usage.append({
            "account_id": a["account_id"],
            "week_start": week_start.isoformat(),
            "weekly_active_users": int(a["licensed_seats"] * rate),
            "integrations_connected": max(1, integ + (wk // 4 if trend > 0 else -(wk // 5))),
        })
with open(OUT / "weekly_usage.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(usage[0].keys()))
    w.writeheader(); w.writerows(usage)

SUBJECTS = [
    "SSO login failing for admin users", "Okta integration not syncing users",
    "Connector to Salesforce shows auth error", "API token expired for integration",
    "Too many alerts from new detection rule", "Question about a risky OAuth app alert",
    "Dashboard loads slowly", "Report export timing out",
    "How do we add a new workspace?", "Need help understanding a posture finding",
    "Billing contact change", "Request for training session for new admins",
]
PRIORITY = ["P1", "P2", "P3", "P4"]
tickets = []
for t in range(320):
    a = random.choice(accounts[:40])
    created = TODAY - timedelta(days=random.randint(0, 90))
    status = random.choices(["open", "pending", "solved"], [0.18, 0.12, 0.70])[0]
    tickets.append({
        "ticket_id": f"ZD-{50000 + t}",
        "account_id": a["account_id"],
        "created_date": created.isoformat(),
        "priority": random.choices(PRIORITY, [0.05, 0.2, 0.5, 0.25])[0],
        "subject": random.choice(SUBJECTS),
        "status": status,
        "first_response_hours": round(random.uniform(0.3, 30), 1),
    })
tickets.append({"ticket_id": "ZD-59999", "account_id": "ACC-9999", "created_date": TODAY.isoformat(),
                "priority": "P3", "subject": "Dashboard loads slowly", "status": "open",
                "first_response_hours": 2.0})  # planted: orphan ticket
with open(OUT / "tickets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tickets[0].keys()))
    w.writeheader(); w.writerows(tickets)

print(f"Wrote {len(accounts)} accounts, {len(usage)} usage rows, {len(tickets)} tickets to {OUT}")
