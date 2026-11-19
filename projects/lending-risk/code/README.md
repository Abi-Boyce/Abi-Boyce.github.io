# Approval vs. loss: LendingClub 2007–2011

SQL (DuckDB) and Python (scikit-learn) behind the report at
https://abi-boyce.github.io/projects/lending-risk/

**Data:** LendingClub's public loan file for 2007–2011 (`LoanStats3a.csv`, 42,538 rows).
Put it in `../raw/` next to this folder. Only finished loans (Fully Paid or Charged Off)
under the standard credit policy are used: 39,747 loans.

**Run, in order:**
1. `01_load.sql` – load and clean (run in DuckDB, database `../lend.duckdb`)
2. `02_analysis.sql` – portfolio, grade/term, purpose, inquiries, vintage queries
3. `python 03_model.py` – default model, approval tradeoff, calibration, adverse action reasons, counter-offer test
4. `python 04_export.py` – writes `report_data.json`, which the report page reads

**Choices worth knowing:**
- Payment columns (total_pymnt, recoveries, last payment) are left out of the model because they leak the outcome.
- State and zip code are left out because location can act as a proxy for protected characteristics.
- Train on 2007–2010 loans, test on 2011 loans, so the model is judged on applicants it hasn't seen.

Built with AI assistance (Claude); every result was re-run and spot-checked against separate queries.
