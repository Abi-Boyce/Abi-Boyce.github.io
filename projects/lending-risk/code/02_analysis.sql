-- Q1. Portfolio overview
SELECT count(*) AS loans, round(sum(funded_amnt)/1e6,1) AS funded_musd,
       round(100*avg(bad),1) AS bad_rate_pct,
       round(100*sum(CASE WHEN bad=1 THEN funded_amnt-total_rec_prncp-recoveries ELSE 0 END)/sum(funded_amnt),1) AS net_principal_loss_pct
FROM loans;

-- Q2. Bad rate and losses by grade and term
SELECT grade, term_months, count(*) AS loans,
       round(100*avg(bad),1) AS bad_rate_pct,
       round(avg(int_rate),1) AS avg_rate_pct,
       round(100*(sum(total_pymnt)-sum(funded_amnt))/sum(funded_amnt),1) AS net_return_pct
FROM loans GROUP BY 1,2 ORDER BY 1,2;

-- Q3. Bad rate by loan purpose (largest groups)
SELECT purpose, count(*) AS loans, round(100*avg(bad),1) AS bad_rate_pct
FROM loans GROUP BY 1 HAVING count(*) >= 500 ORDER BY bad_rate_pct DESC;

-- Q4. Credit inquiries in the last 6 months, within the same grade
SELECT grade, CASE WHEN inq_last_6mths >= 3 THEN '3+' ELSE CAST(CAST(inq_last_6mths AS INT) AS VARCHAR) END AS inquiries,
       count(*) AS loans, round(100*avg(bad),1) AS bad_rate_pct
FROM loans WHERE grade IN ('A','B','C','D') GROUP BY 1,2 ORDER BY 1,2;

-- Q5. Vintage view: bad rate by issue year
SELECT year(issue_month) AS issue_year, count(*) AS loans, round(100*avg(bad),1) AS bad_rate_pct
FROM loans GROUP BY 1 ORDER BY 1;
