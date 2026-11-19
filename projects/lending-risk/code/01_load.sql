-- Load LendingClub 2007-2011 loans (LoanStats3a.csv) into DuckDB.
-- The file has one note line before the header and a few summary lines at the end.
CREATE OR REPLACE TABLE raw AS
SELECT * FROM read_csv('../raw/LoanStats3a.csv', skip=1, header=true, all_varchar=true,
                       ignore_errors=true, null_padding=true);

-- Clean, typed table of finished loans only (Fully Paid or Charged Off).
-- Rows marked "Does not meet the credit policy" are older loans issued under
-- different rules, so they are kept out of the main analysis.
CREATE OR REPLACE TABLE loans AS
SELECT
  CAST(id AS BIGINT)                                         AS id,
  CAST(loan_amnt AS DOUBLE)                                  AS loan_amnt,
  CAST(funded_amnt AS DOUBLE)                                AS funded_amnt,
  CAST(trim(replace(term,' months','')) AS INTEGER)          AS term_months,
  CAST(replace(trim(int_rate),'%','') AS DOUBLE)             AS int_rate,
  CAST(installment AS DOUBLE)                                AS installment,
  grade, sub_grade,
  emp_length, home_ownership,
  CAST(annual_inc AS DOUBLE)                                 AS annual_inc,
  verification_status,
  strptime(issue_d, '%b-%Y')::DATE                           AS issue_month,
  loan_status, purpose, addr_state,
  CAST(dti AS DOUBLE)                                        AS dti,
  CAST(delinq_2yrs AS DOUBLE)                                AS delinq_2yrs,
  CAST(inq_last_6mths AS DOUBLE)                             AS inq_last_6mths,
  CAST(open_acc AS DOUBLE)                                   AS open_acc,
  CAST(pub_rec AS DOUBLE)                                    AS pub_rec,
  CAST(revol_bal AS DOUBLE)                                  AS revol_bal,
  CAST(replace(trim(revol_util),'%','') AS DOUBLE)           AS revol_util,
  CAST(total_acc AS DOUBLE)                                  AS total_acc,
  CAST(total_pymnt AS DOUBLE)                                AS total_pymnt,
  CAST(total_rec_prncp AS DOUBLE)                            AS total_rec_prncp,
  CAST(recoveries AS DOUBLE)                                 AS recoveries,
  (loan_status = 'Charged Off')::INTEGER                     AS bad
FROM raw
WHERE loan_status IN ('Fully Paid','Charged Off')
  AND id IS NOT NULL AND issue_d IS NOT NULL;
