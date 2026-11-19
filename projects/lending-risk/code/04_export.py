"""Run the SQL analysis and save every result the report page uses to one JSON file."""
import json, duckdb
con = duckdb.connect('../lend.duckdb', read_only=True)
qs = [s for s in open('02_analysis.sql').read().split(';') if 'SELECT' in s]
names = ['overview', 'grade_term', 'purpose', 'inquiries', 'vintage']
out = {n: con.execute(q).df().to_dict('records') for n, q in zip(names, qs)}
out['model'] = json.load(open('../model_results.json'))
json.dump(out, open('../report_data.json', 'w'), default=str)
print(json.dumps(out)[:600])
