"""Run the 30 open cases, save results for the app, and score against the answer key.  python scripts/run_open.py"""
import os, sys, json, glob, csv
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from copilot import pipeline
raws = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "data/open_cases/*.json")))]
with ThreadPoolExecutor(6) as ex: results = list(ex.map(pipeline.run_case, raws))
key = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "tests/open_cases_answer_key.csv")))}
ok = 0; rows = []
for r in results:
    cid = r["case"]["case_id"]; exp = key[cid]["tool_recommendation"]; got = r["result"]["outcome"]; hit = exp == got; ok += hit
    r["expected"] = exp; r["what_it_tests"] = key[cid]["what_it_tests"]
    rows.append((cid, exp, got, "ok" if hit else "MISS", ",".join(f["code"] for f in r["flags"])))
    print(*rows[-1], sep=" | ")
print(f"\n{ok}/{len(results)} match the answer key")
json.dump(results, open(os.path.join(ROOT, "public/data/open_cases.json"), "w"))
json.dump(dict(matched=ok, total=len(results), rows=rows), open(os.path.join(ROOT, "public/data/open_score.json"), "w"))
