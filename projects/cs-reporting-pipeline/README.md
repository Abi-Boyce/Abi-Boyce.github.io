# CS reporting & automation pipeline (sample project)

A small, working version of the reporting and automation layer a Customer Success Operations team runs. It takes fictional CRM, support-desk and product-usage data, then produces:

- an **account health score** with every component visible
- a **renewal watchlist** with a next action for each account
- a **ticket triage queue**, where rules handle the clear cases and an LLM plus a person handle the rest
- a **data-quality report** that catches problems before anyone trusts the numbers
- **AI-ready QBR inputs**: minimized JSON per at-risk account, plus a guarded prompt for drafting the brief
- a one-page **executive summary**

All data is invented. Built with AI assistance (Claude), then run, checked and documented by me.

## Run it

```
pip install duckdb
python generate_sample_data.py   # writes data/*.csv
python pipeline.py               # writes output/*
```

## How it's built

| Step | Where | Deterministic or AI? |
| --- | --- | --- |
| Load sources | `pipeline.py` (DuckDB) | Deterministic |
| Clean + model the mart | `sql/mart.sql` | Deterministic |
| Data-quality checks | `pipeline.py`, section 1 | Deterministic |
| Health score + watchlist | `sql/mart.sql` | Deterministic |
| Ticket triage | Keyword rules in `pipeline.py`, LLM only for leftovers | Rules first, AI second |
| QBR brief | `prompts/qbr_brief_prompt.md` on `output/qbr_inputs/*.json` | AI drafts, a person approves |

**The rule:** numbers come from SQL, words can come from AI, and a person approves anything a customer or executive sees.

## Results on the sample data

- 40 accounts scored: 14 Healthy, 15 Watch, 11 At risk ($1.86M ARR at risk)
- 2 renewals in the next 120 days flagged with next actions
- 62 of 95 open tickets (65%) routed automatically by rules; 33 sent for LLM suggestion and human review
- 4 planted data problems caught: a missing renewal date, a duplicate account, an orphan ticket and missing usage weeks

## Next automation I'd build (designed, not built yet)

When a P1/P2 ticket opens for an account that is At risk or renewing within 90 days:
1. **Zendesk trigger** → integration platform (e.g., Zapier or Workato)
2. **Look up** the account's health and renewal date from the mart
3. **Post to the account's Slack channel**, tagging the CSM and TAM, with the ticket link and health context
4. **Log a Salesforce task** on the renewal opportunity, so the risk shows up in forecast reviews

## Docs

- `docs/data_dictionary.md`: sources, mart views and how the score works
- `docs/access_model.md`: who sees what, and what goes to an LLM
