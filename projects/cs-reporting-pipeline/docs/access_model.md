# Proposed data access model

Customer-tenant data is sensitive, especially at a security company. This is a proposal for Business Systems and Security to review and implement. It is not a final design.

## Principles

1. **Least privilege:** people see the accounts and fields their job needs, nothing more.
2. **Aggregate before AI:** only minimized, aggregated fields go to an LLM. No user names, emails, IP addresses or raw ticket text.
3. **Auditable:** every query against the mart is logged, along with who ran it and why.

## Who sees what

| Role | Accounts | Fields | AI use |
| --- | --- | --- | --- |
| CSM | Own book of business | Health score and components, renewals, ticket counts | QBR brief drafts for own accounts |
| TAM | Assigned accounts | Above, plus ticket subjects and diagnostics | Triage suggestions for assigned tickets |
| Support | All accounts, ticket data only | Ticket fields; no ARR or renewal data | Triage suggestions |
| CS leadership | All accounts | Aggregates and watchlist; drill-down on request | Exec summary drafts |
| Exec / board reporting | All accounts, aggregated | Totals by band, segment and ARR only | None needed |

## Controls to request

- Row-level filters on `csm_owner` / assigned TAM, enforced in the warehouse rather than in each dashboard
- Column masking on customer contact fields
- A service account for automations with read-only access to the mart views (no raw tables)
- Quarterly access review with the CS operations owner
