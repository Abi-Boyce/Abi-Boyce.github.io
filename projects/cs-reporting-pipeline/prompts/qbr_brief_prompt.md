# LLM step: draft a QBR/EBR brief from one account's JSON

**Input:** one file from `output/qbr_inputs/` (aggregates only: no user names, emails or raw ticket text).
**Output:** a draft for the CSM or TAM to edit. It is never sent to a customer automatically.

## Prompt

You are helping a Customer Success Manager prepare for a business review with a customer of a SaaS security platform.

Use ONLY the numbers in the JSON below. Do not invent metrics, dates, names or causes. If something the brief needs is missing from the JSON, write "Not in data" instead of guessing.

Write, in plain language:
1. **Headline** (one sentence): the account's health and the single most important change.
2. **What the data shows** (3 bullets): adoption now vs. before, integration coverage vs. target, and support load.
3. **Likely questions from the customer** (2 bullets).
4. **Recommended next steps for the CSM** (3 bullets), each tied to a number in the data.
5. **Confidence note** (one line): what a person should check before this goes into a deck.

JSON:
```
{{account_json}}
```

## Review checklist (the human step)

- Every number in the draft matches the JSON exactly.
- No cause is stated as fact unless the CSM has confirmed it.
- Tone fits the relationship. The CSM edits before anything is shared.
