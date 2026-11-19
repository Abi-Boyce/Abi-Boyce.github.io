"""Probability-of-default model and approval tradeoff on LendingClub 2007-2011 loans.

Uses only information known when the application is made. Payment columns
(total_pymnt, recoveries, ...) are left out because they leak the outcome.
Location columns (state, zip) are left out on purpose: they can act as a
proxy for protected characteristics under fair lending rules.

Time-based split: train on loans issued 2007-2010, test on 2011 loans,
the way a model would be used on future applicants.
"""
import json, duckdb, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

con = duckdb.connect('../lend.duckdb', read_only=True)
df = con.execute("SELECT * FROM loans").df()

sub_order = sorted(df.sub_grade.dropna().unique())          # A1 < A2 < ... < G5
df['sub_grade_n'] = df.sub_grade.map({s: i for i, s in enumerate(sub_order)})
def emp_years(s):
    s = str(s)
    if s.startswith('<'): return 0.0
    if s.startswith('10+'): return 10.0
    return float(s.split()[0]) if s[:1].isdigit() else np.nan   # 'n/a' -> missing
df['emp_years'] = df.emp_length.map(emp_years)
df['log_income'] = np.log1p(df.annual_inc)
df['loan_to_income'] = df.loan_amnt / df.annual_inc
df['term60'] = (df.term_months == 60).astype(int)
df['renter'] = (df.home_ownership == 'RENT').astype(int)
df['verified'] = (df.verification_status != 'Not Verified').astype(int)
df['small_business'] = (df.purpose == 'small_business').astype(int)
df['year'] = pd.to_datetime(df.issue_month).dt.year

FEATS = ['sub_grade_n', 'term60', 'log_income', 'loan_to_income', 'dti', 'revol_util',
         'inq_last_6mths', 'delinq_2yrs', 'pub_rec', 'open_acc', 'total_acc',
         'emp_years', 'renter', 'verified', 'small_business']
LABELS = {'sub_grade_n': 'Lower credit sub-grade', 'term60': '60-month term', 'log_income': 'Higher income',
          'loan_to_income': 'Loan size vs. income', 'dti': 'Debt-to-income', 'revol_util': 'Credit card utilization',
          'inq_last_6mths': 'Recent credit inquiries', 'delinq_2yrs': 'Delinquencies (2 yrs)', 'pub_rec': 'Public records',
          'open_acc': 'Open accounts', 'total_acc': 'Total accounts', 'emp_years': 'Years employed',
          'renter': 'Rents home', 'verified': 'Income verified', 'small_business': 'Small business loan'}

d = df.dropna(subset=FEATS + ['bad']).copy()
train, test = d[d.year <= 2010], d[d.year == 2011]
sc = StandardScaler().fit(train[FEATS])
m = LogisticRegression(max_iter=2000).fit(sc.transform(train[FEATS]), train.bad)
p = m.predict_proba(sc.transform(test[FEATS]))[:, 1]

auc_model = roc_auc_score(test.bad, p)
auc_grade = roc_auc_score(test.bad, test.sub_grade_n)        # grade alone, as a baseline

# Approval tradeoff: approve the safest X% of 2011 applicants, by model vs. by grade.
def bad_rate_at(score, share):
    cut = np.quantile(score, share)
    keep = score <= cut
    return float(test.bad[keep].mean()), int(keep.sum())
rng = np.random.default_rng(0)
grade_score = test.sub_grade_n.values + rng.uniform(0, 0.01, len(test))  # break ties within a sub-grade
curve = []
for share in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    bm, _ = bad_rate_at(p, share); bg, n = bad_rate_at(grade_score, share)
    curve.append({'approve_pct': int(share * 100), 'bad_rate_model': round(100 * bm, 1),
                  'bad_rate_grade': round(100 * bg, 1), 'approved': n})

# Calibration: predicted vs. actual bad rate by risk decile
test = test.assign(p=p, decile=pd.qcut(p, 10, labels=False) + 1)
cal = test.groupby('decile').agg(pred=('p', 'mean'), actual=('bad', 'mean'), n=('bad', 'size')).reset_index()

# Adverse action reasons: for applicants the model would decline at an 80% approval
# rate, the factor that pushed their risk up the most (coefficient x standardized value).
# Grade is left out of the reasons because it is a summary score, not a reason a person can act on.
Z = sc.transform(test[FEATS]) * m.coef_[0]
declined = test.p.values > np.quantile(test.p.values, 0.8)
reason_feats = [i for i, f in enumerate(FEATS) if f != 'sub_grade_n']
top = [FEATS[reason_feats[j]] for j in np.argmax(Z[declined][:, reason_feats], axis=1)]
REASON = dict(LABELS, log_income='Income too low', verified='Income not verified',
              emp_years='Years employed', delinq_2yrs='Delinquencies (2 yrs)', dti='Debt-to-income')
reasons = pd.Series(top).map(REASON).value_counts()
reasons = [{'reason': k, 'pct': round(100 * v / declined.sum(), 1)} for k, v in reasons.items()]

# Counter-offer test: if a declined 60-month applicant were offered a 36-month term
# instead, would their predicted risk fall under the approval cutoff?
cut80 = np.quantile(test.p.values, 0.8)
dec60 = test[declined & (test.term60 == 1).values].copy()
alt = dec60[FEATS].copy(); alt['term60'] = 0
alt['loan_to_income'] = alt['loan_to_income']  # same amount; only the term changes
p36 = m.predict_proba(sc.transform(alt))[:, 1]
counter = {'declined_60m': len(dec60), 'pass_at_36m': int((p36 <= cut80).sum()),
           'actual_bad_rate_declined_60m': round(100 * dec60.bad.mean(), 1)}

coefs = sorted([{'feature': LABELS[f], 'coef': round(float(c), 3)} for f, c in zip(FEATS, m.coef_[0])],
               key=lambda x: -abs(x['coef']))

out = {'train_n': len(train), 'test_n': len(test), 'test_bad_rate': round(100 * test.bad.mean(), 1),
       'auc_model': round(auc_model, 3), 'auc_grade': round(auc_grade, 3), 'curve': curve,
       'calibration': [{k: (round(100 * v, 1) if k in ('pred', 'actual') else int(v)) for k, v in r.items()} for r in cal.to_dict('records')],
       'coefs': coefs, 'declined_n': int(declined.sum()), 'reasons': reasons, 'counter_offer': counter}
json.dump(out, open('../model_results.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
