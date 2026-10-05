"""Charts for the documentation, computed from the academy data pack (not in this repo). Output is committed in docs/charts/.
python scripts/charts.py /path/to/Bellcourt_Data_Pack"""
import sys, os, csv, json, collections, datetime as dt
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "docs", "charts")
PACK = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/Bellcourt_Data_Pack"); OPS = os.path.join(PACK, "04_operational_data")
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#c3c2b7", "xtick.color": "#898781", "ytick.color": "#898781",
                     "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.06})
BLUE, ORANGE, AQUA, YELLOW, GREY, INK, SEC, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#c3c2b7", "#0b0b0b", "#52514e", "#e1e0d9"
rows = list(csv.DictReader(open(os.path.join(OPS, "pa_requests_2025_2026.csv"))))
for r in rows:
    d = dt.datetime.strptime(r["received_ts"], "%Y-%m-%d %H:%M"); r["q"] = f"{d.year} Q{(d.month - 1) // 3 + 1}"
    for k in ("intake_hours", "pend_for_info_hours", "nurse_review_hours", "md_review_hours"): r[k] = float(r[k])
    r["met"] = r["sla_met"] == "True"; r["complete"] = r["complete_on_receipt"] == "True"
ma = [r for r in rows if r["product"] == "MA" and r["urgency"] == "STANDARD"]; qs = sorted({r["q"] for r in ma})
st = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(OPS, "nurse_staffing_weekly.csv"))):
    d = dt.datetime.strptime(r["week_start"], "%Y-%m-%d"); st[f"{d.year} Q{(d.month - 1) // 3 + 1}"].append(float(r["nurse_fte_actual"]))
fte = [sum(st[q]) / len(st[q]) for q in qs]; ont = [100 * sum(r["met"] for r in ma if r["q"] == q) / sum(1 for r in ma if r["q"] == q) for q in qs]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 3.1), sharex=True, gridspec_kw={"hspace": 0.5}); x = range(len(qs))
a1.plot(x, fte, color=BLUE, lw=2, marker="o", ms=5); a1.axhline(58, color=GREY, lw=1); a1.text(len(qs) - 1, 58.3, "Budget 58", ha="right", fontsize=8, color=SEC); a1.set_ylim(46, 60.5)
a1.set_title("Nurse reviewers in post (FTE)", loc="left", fontsize=9, fontweight="bold"); [a1.text(i, fte[i] - 2.7, f"{fte[i]:.1f}", ha="center", fontsize=8.5) for i in (0, len(qs) - 1)]
a2.plot(x, ont, color=BLUE, lw=2, marker="o", ms=5); a2.axhline(97, color=GREY, lw=1); a2.text(len(qs) - 1, 97.3, "Contract standard 97%", ha="right", fontsize=8, color=SEC); a2.set_ylim(80, 100.5)
a2.set_title("Riverbend Medicare Advantage standard decisions made on time (%)", loc="left", fontsize=9, fontweight="bold"); [a2.text(i, ont[i] - 3.7, f"{ont[i]:.1f}%", ha="center", fontsize=8.5) for i in (0, len(qs) - 2, len(qs) - 1)]
for a in (a1, a2): a.yaxis.grid(True, color=GRID, lw=0.7); a.set_axisbelow(True); a.spines["left"].set_visible(False); a.tick_params(axis="y", length=0)
a2.set_xticks(list(x)); a2.set_xticklabels(qs); fig.savefig(os.path.join(OUT, "staffing.png")); plt.close(fig)

groups = [("Arrived complete", [r for r in ma if r["complete"]]), ("Arrived incomplete,\ndecided on time", [r for r in ma if not r["complete"] and r["met"]]), ("Arrived incomplete,\ndecided late", [r for r in ma if not r["complete"] and not r["met"]])]
stages = [("intake_hours", "Intake and keying", BLUE), ("pend_for_info_hours", "Waiting for missing information", ORANGE), ("nurse_review_hours", "Nurse review", AQUA), ("md_review_hours", "Physician review", YELLOW)]
fig, ax = plt.subplots(figsize=(7.2, 2.3))
for y, (lab, g) in zip((2, 1, 0), groups):
    left = 0
    for col, name, c in stages:
        v = sum(r[col] for r in g) / len(g); ax.barh(y, v, left=left, height=0.5, color=c, edgecolor="white", lw=1.5, label=name if y == 2 else None)
        if v >= 14: ax.text(left + v / 2, y, f"{v:.0f}h", ha="center", va="center", fontsize=8, fontweight="bold", color="white" if c in (BLUE, ORANGE) else INK)
        left += v
    ax.text(left + 3, y, f"{left:.0f}h total", va="center", fontsize=8.5, color=SEC)
ax.axvline(168, color=INK, lw=1); ax.text(171, 2.42, "7-day deadline (168h)", fontsize=8)
ax.set_yticks((2, 1, 0)); ax.set_yticklabels([f"{l} ({len(g)})" for l, g in groups], color=INK); ax.set_xlim(0, 235); ax.set_ylim(-0.5, 2.8); ax.set_xlabel("Average hours from receipt to decision")
ax.xaxis.grid(True, color=GRID, lw=0.7); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
ax.legend(loc="upper center", bbox_to_anchor=(0.42, -0.26), ncol=4, frameon=False, fontsize=8, handlelength=1); fig.savefig(os.path.join(OUT, "hours.png")); plt.close(fig)

qa = collections.Counter(r["error_type"] for r in csv.DictReader(open(os.path.join(OPS, "qa_audit_sample_2026.csv"))))
items = [("Memo overrode the approved policy", qa["MEMO_CONFLICT"], 1), ("Retired policy version applied", qa["OUTDATED_POLICY_VERSION"], 1), ("Client plan rule missed", qa["CLIENT_RULE_MISSED"], 1), ("Clinical facts misread", qa["CRITERIA_MISREAD"], 0), ("Denied instead of asking for information", qa["MISSING_INFO_NOT_REQUESTED"], 0)]
fig, ax = plt.subplots(figsize=(7.2, 2.0))
for y, (lab, v, rule) in zip(range(4, -1, -1), items): ax.barh(y, v, height=0.5, color=BLUE if rule else GREY); ax.text(v + 0.3, y, str(v), va="center", fontsize=9)
ax.set_yticks(range(4, -1, -1)); ax.set_yticklabels([i[0] for i in items], color=INK); ax.set_xticks([0, 5, 10, 15, 20]); ax.set_xlim(0, 21); ax.set_xlabel("Audited cases with this error (52 errors in 120 audited cases)")
ax.xaxis.grid(True, color=GRID, lw=0.7); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
ax.legend(handles=[Patch(color=BLUE, label="Wrong rule applied: 39 of 52"), Patch(color=GREY, label="Other: 13 of 52")], loc="lower right", frameon=False, fontsize=8.5, handlelength=1); fig.savefig(os.path.join(OUT, "qa_errors.png")); plt.close(fig)

S = json.load(open(os.path.join(ROOT, "data/results/eval.json")))["summary"]; by = S["by_error_type"]
cats = [("All 120 audited cases", S["tool_correct"], S["human_correct"], S["n"]), ("Memo conflict cases", by["MEMO_CONFLICT"][0], 0, by["MEMO_CONFLICT"][1]), ("Retired-version cases", by["OUTDATED_POLICY_VERSION"][0], 0, by["OUTDATED_POLICY_VERSION"][1]), ("Client-rule cases", by["CLIENT_RULE_MISSED"][0], 0, by["CLIENT_RULE_MISSED"][1])]
fig, ax = plt.subplots(figsize=(7.2, 2.1))
for i, (lab, t, h, n) in enumerate(cats):
    y = len(cats) - 1 - i; ax.barh(y + 0.2, 100 * t / n, height=0.36, color=BLUE, label="Review Copilot" if i == 0 else None); ax.barh(y - 0.2, 100 * h / n, height=0.36, color=GREY, label="Original human decision" if i == 0 else None)
    ax.text(100 * t / n + 1, y + 0.2, f"{t} of {n}", va="center", fontsize=8.5); ax.text(100 * h / n + 1, y - 0.2, f"{h} of {n}", va="center", fontsize=8.5)
ax.axvline(95, color=INK, lw=1); ax.text(94, len(cats) - 0.45, "Standard 95%", ha="right", fontsize=8)
ax.set_yticks(range(len(cats) - 1, -1, -1)); ax.set_yticklabels([c[0] for c in cats], color=INK); ax.set_xlim(0, 118); ax.set_ylim(-0.6, len(cats) - 0.2); ax.set_xlabel("Decisions that agree with the QA auditor (%)")
ax.xaxis.grid(True, color=GRID, lw=0.7); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0); ax.legend(loc="lower right", frameon=False, fontsize=8.5, handlelength=1)
fig.savefig(os.path.join(OUT, "results.png")); plt.close(fig); print("charts written", os.listdir(OUT))
