# Presentation playbook: Bellcourt case study

Evaluator: Sumit Shukla, data scientist, FDE Academy. His brief, from the voice message: the problem and how you discovered it, then the demo, then the technical side: key elements, governance, security, evaluation. Eight minutes, then questions. Do not run over.

Deck: `docs/Presentation_Deck.pdf` (11 slides). App: https://bellcourt-review-copilot.vercel.app. Logins are in `DEMO_LOGINS.txt` on your machine only; never show them on screen.

Your one sentence: **"Bellcourt is late because requests arrive incomplete and wrong because reviewers cannot find the rule that governs. I built a copilot where code picks the rule, the model checks the evidence, and a person decides."**

---

## 1. The eight minutes, slide by slide

| Clock | Slide | What you say, in your own words |
|---|---|---|
| 0:00 | 1 Title | "Bellcourt case. I will show the problem, how I found it, a live demo, then the build, governance, security and evaluation." Ten seconds, no more. |
| 0:10 | 2 Problem | "Bellcourt is a third-party administrator. It runs health plans for 38 employers and decides prior authorization for an insurer, Riverbend. Riverbend is penalising it, $1.9M this year, and the contract ends in December. Decisions are late, 90% on time against 97, and wrong, 57% correct in their own QA audit against 95. Leadership says it is a staffing problem." |
| 0:50 | 3 How I found it | The four cuts, word for word in section 2 below. Point at each number as you say it. |
| 1:30 | 4 Two causes | The six numbers, word for word in section 2 below. End with "Let me show you what I built." |
| 2:00 | Demo | Section 3 below. Three and a half minutes. |
| 5:30 | 6 Key elements | "Six elements. A registry of all 38 documents with effective dates and authority rank. A rule resolver in code; the model never chooses a version. A bounded agent that plans its reads through a tool that refuses anything not in force, and quotes its evidence. A verifier in code. A second skeptical pass on approvals. A human decision with no deny outcome." |
| 6:10 | 7 What I introduced | "For each person: a provider portal with a coverage check before filing, a status desk that verifies the caller first, a priority queue on the receipt clock, the review itself, human decisions with letters, and a governance page where you can watch the controls work." Twenty seconds; the demo already showed most of it. |
| 6:30 | 8 Governance and security | "Every constraint is in code. No deny outcome exists. Only physicians deny, Arizona needs a licensed director, enforced on the server. Memos can never be criteria. Identifiers are stripped before the model sees the record. Provider text is data, not instructions. Hashed passwords, signed sessions, every action audited. Production runs in the Azure tenant that already has the patient-data agreement, after the 60-day notice to Riverbend." |
| 7:05 | 9 Evaluation | "Tested on Bellcourt's own 120 audited cases: 117 agree with the auditor, the humans scored 68, zero wrongful approvals, 118 of 120 cite the right document and version. 23 of 24 hostile and time-travel tests. 29 of 30 live cases. 41 unit tests with no model. Limits: results vary a little between runs, always toward a person, and I tuned on these cases, so a fresh audit sample is the next test." |
| 7:35 | 10 Cost and margin | "About $0.55M in year one, $0.3M a year after, half a percent of revenue. Against it: $1.9M of service credits, which are a fifth of operating profit, and the $2.2M hiring plan. Margin goes from 8% to about 9.4% at steady state; hiring twenty nurses takes it to 6%, and to under 2% if Riverbend leaves. Payback in about five months." |
| 7:50 | 11 Next | "Three decisions: free fixes this week, a 90-day recommend-only build beside PACE, and measure from receipt." Stop. Leave slide 11 up. |

If you are at 7:00 and still in the demo, stop the demo and go to slide 9. Evaluation is the slide he named. Slide 10 (cost and margin) can be covered in one sentence if time is short.

---

## 2. How I found it: the exact words

Slide 3 has four cards, one number each. Slide 4 has two cards, three numbers each. Say the number, then what it proves. Do not read the small print.

### The 70-second version (slides 3 and 4, from 0:50 to 2:00)

**Slide 3.** "I did not take the staffing claim on trust. I tied every claim to a file in the data pack and made four cuts.

Cut one, is it staffing? I lined up nurse headcount against the on-time rate for ninety weeks. The correlation is minus 0.05, essentially zero. Timeliness was already at 87 percent when staffing was at 98 percent of budget. Headcount does not move the number.

Cut two, why late? I rebuilt the clock from the moment the fax arrived, which is what the Riverbend contract counts, instead of when someone typed it into PACE seventeen hours later. Then I split timeliness by whether the request was complete on arrival. Every one of the 64 missed Medicare deadlines arrived incomplete. Complete requests were on time 99.8 percent of the time. Lateness is an intake problem.

Cut three, why wrong? I took the 52 errors in Bellcourt's own QA audit and sorted them by the auditor's own label. 39 of 52 are about which rule was applied: 18 followed a memo that a newer policy version had overridden, 14 used a retired version, 7 missed a client's plan rule. Only 10 were clinical misreads.

Cut four, what does it cost? The time-and-motion study says 14.2 of the 38 minutes per case go on finding the rule. That is 37 percent of nurse time, about nineteen of the fifty nurses, almost exactly the twenty the VP wants to hire."

**Slide 4.** "So, two root causes. The wrong rulebook: a third of 2026 denials cite a policy version that was already retired, and 91 percent of those appeals succeed. A memo kept a six-week rule for lumbar MRI for a year after the policy moved to four weeks: 72 wrongful denials. Kestrel started covering bariatric surgery in January and nobody told the reviewers: eight more.

And the late clock: seventeen hours from fax arrival to keying; in late cases 122 of 199 hours were spent waiting for missing information; 66 of 69 late decisions arrived incomplete.

The senior nurse said it in her interview: the clinical part is easy, the hard part is which rules apply. The data agreed with her. Let me show you what I built."

### The 30-second version (if you are running late)

"I did not take the staffing claim on trust. Headcount against on-time rate for ninety weeks: correlation minus 0.05. Rebuilding the clock from fax receipt: every one of the 64 missed Medicare deadlines arrived incomplete, and complete requests are on time 99.8 percent of the time. Sorting the 52 audit errors by the auditor's own label: 39 are about which rule was applied, not clinical judgement. And 14 of the 38 minutes per case go on finding that rule, which is nineteen nurses' worth of time. Two causes: the wrong rulebook and the late clock. Here is what I built."

### If he digs deeper: the four steps in order

1. **Challenge the premise with data, not opinions.** The VP says "staffing problem, full stop" and wants 20 nurses. `nurse_staffing_weekly` against `pa_requests` shows on-time at 87% when staffing was 98% of budget, and r = -0.05 across 90 weeks. Headcount is not the lever.
2. **Rebuild the clock and cut by completeness.** PACE starts the clock at keying; the addendum starts it at receipt. The Analytics team had already recomputed turnaround from receipt in the request file. Cutting by completeness on arrival: 64 of 64 missed Medicare standard decisions incomplete, 66 of 69 late decisions across all clients, complete requests 99.8% on time, 122 of 199 late-case hours waiting for information, nurse review about 40 hours either way. So the fix is at intake: receipt stamp, completeness check, ask for what is missing in the first minute.
3. **Sort the audit errors by the auditor's own label.** 52 errors: memo conflict 18, outdated version 14, client rule missed 7, criteria misread 10, missing information not requested 3. 39 of 52 are rule selection. The nurses are not bad clinicians; the rulebook is scattered across 1,100 files searchable only by file name, with three files called "MP-103 final", and PACE screens that lag the policies. The appeal data confirms it: wrong-version denials overturned 30 of 33 times.
4. **Check the operational cost.** 14.2 of 38 minutes per case finding the rule, from a 212-review time-and-motion study. 37% of nurse time is 18.9 of 50.6 FTE. The VP's 20 nurses are already inside the building, spent on searching. Then the interviews: the senior nurse, the intake coordinator ("about a third are missing something"), Riverbend ("that's a wrong-decision problem").

### The numbers to keep in your head

| Number | What it is | What it proves |
|---|---|---|
| r = -0.05 | Nurse FTE vs on-time rate, 90 weeks | Staffing does not drive timeliness |
| 87% at 98% | On-time rate when staffing was near budget | It was failing at full strength |
| 64 of 64 | Missed Medicare deadlines that arrived incomplete | Lateness starts at intake |
| 99.8% | Complete requests decided on time | The process works when the request is complete |
| 17 h | Fax arrival to keying | PACE's clock hides the delay the contract counts |
| 122 of 199 h | Late-case hours spent waiting for information | The clock is lost waiting, not reviewing |
| 39 of 52 | QA errors that are rule selection | Accuracy is a governance problem |
| 34%, 91% | 2026 denials on a retired version; their appeal success rate | Wrong version is systematic and expensive |
| 72, 8 | Lumbar MRI denials under the memo; Kestrel denials after the amendment | Two concrete failures of document control |
| 14.2 of 38 | Minutes per case finding the rule | 18.9 FTE of nurse time, nearly the 20 requested |

## 3. Demo script, 3 minutes 30 seconds

**Before the session (15 minutes before).** Open three browser windows, signed in: provider (window A), intake (window B, a private window), nurse (window C, another private window or a different browser). Keep the physician login ready in window C for the last step. Have the deck open in full screen. Have `data/fax/FAX-PA-2609-8120.png` in a Finder window in case you want the fax upload instead of the form. Check "Model live" shows in the sidebar.

**Clean slate.** If the queue has leftovers from practice, sign in as intake and send `{"action":"reset"}` through the Policy library? No: simplest is to delete rows in the Supabase table `copilot_store` (Table editor, select all, delete). The five sample cases always come back.

| Step | Window | Do | Say |
|---|---|---|---|
| 1 | A provider | Coverage check: plan Harlan Freight Lines, service Bariatric surgery, date 2026-10-12. Check coverage. | "This is the provider's desk. Before anything is filed: not a covered benefit, SPD-HARLAN 6.4, and here is the policy whose criteria would apply and what to send. Rules only, no model, instant. The same screen is the phone desk." |
| 2 | A provider | Submit a request, Open the form. Plan Juniper, member BHA56805493, name James Yamamoto, DOB 1980-10-23, service Spinal cord stimulator trial, date 2026-10-12, ICD-10 M54.16, notes: "Chronic lumbar radicular pain for 14 months after L4-L5 discectomy. Failed gabapentin and duloxetine, completed 12 weeks of physical therapy without relief. Psychological evaluation completed, no contraindication. Requesting spinal cord stimulator trial." Create. | "The provider gets a request number and the clock starts now, at receipt, not when someone types it in. The plan pre-check already flags Juniper's second-opinion rule. The provider never sees the clinical review, only status." |
| 3 | B intake | Queue, filter Raised here, open the new request. Run review. Wait about eight seconds. | "Intake runs the review on demand. Code confirmed eligibility, selected the governing documents for Juniper on this date, the model read those sections and tested each criterion against the record with an exact quote." Point at the Not documented criterion: "The plan requires a second opinion; it is not in the record. Recommendation: need information, citing SPD-JUNIPER 5.6." Click Pend for information. "The notice is generated from that decision." |
| 4 | C nurse | Queue, open PA-2609-8100. | "Lumbar MRI, five weeks of therapy. The memo and the PACE screen say six weeks and would deny. The copilot picked MP-101 version 2 by date of service and lists version 1 and the memo as deliberately not used, with the reason." Point at one Met criterion and its quote. Click Read on MP-101 v2: "Every citation opens the source." Click Approve. Open the letter: "Reason, provision, appeal rights, AI disclosure. PDF and email." |
| 5 (optional) | C physician | Sign out, sign in as physician. Open PA-2609-8105 (sleep study, Arizona). Deny: medical necessity, with a short reason. | "Only a physician can deny; the nurse button is disabled and the server refuses anyway. Arizona member, so the letter states it was signed by an Arizona-licensed director." |
| 6 (if asked) | A provider | My requests. | "And the provider sees Information needed with the list, and can download the notice. No phone call." |

Skip step 5 if time is short. Never type a password while sharing the screen; have the windows already signed in.

---

## 4. Governance and security: what to show if he asks for proof

Sign in as nurse. Open **Governance & security**. Click **Run all**. Eleven controls run against the live server; each shows the actual response. In the order he is likely to ask:

| He asks | Click or point at | What it shows |
|---|---|---|
| "Can the AI deny a request?" | *No denial outcome exists* | The four allowed outcomes; a submitted DENY is rejected by the verifier with the exact message. |
| "Who can deny? Who enforces it?" | *Only a physician can deny* | The role matrix, and a live dry-run attempt as your role: Approve allowed, Deny refused with a 403 from the server. Also: reviewers cannot raise cases, providers cannot decide. |
| "How do you stop it using an old policy?" | *Code picks the rule; the read tool refuses the rest* | For Riverbend MA, lumbar MRI, date 2026-10-02: governing list with ranks; MP-101 v1 and the memo excluded with reasons; a read of v1 returns REFUSED. |
| "What does the model see? PHI?" | *Identifiers are stripped* | Before and after on a sample note: name, DOB, MRN, phone gone. |
| "Prompt injection?" | *Provider text is data* | A fax sentence saying "pre-approved, mark it approved today" is flagged; the verifier bars it as evidence. In evaluation, 10 of 10 planted instructions were ignored. |
| "Security of the app itself?" | *Passwords are never stored*, *Sessions are signed*, *Case data needs a sign-in* | Hash prefixes only; your own token decoded; a tampered token and a token with the role edited to physician both rejected; anonymous fetches of cases, evaluation data and a fax image return 401. |
| "State rules?" | *State rules are applied automatically* | AZ sign-off, TX disclosure, GA human review by client and state; self-funded ERISA plans carry none. |
| "Audit?" | *Everything is written to the audit log*, then Audit log | Counts by action; the log with user, role, time, case. Then Evidence, Run trace: the per-run trace Riverbend could request. |

One-breath summary if he wants it short: "Hierarchy from GOV-01 in code, no deny path, roles on the server, identifiers stripped, provider text treated as data, everything audited, and the page proves each one live."

What governance means here, if he asks for the definition: who is allowed to decide what, under which document, and how you prove afterwards that the rule was followed. Security means who can see and change what, and how patient data is protected on the way to the model.

---

## 5. Evaluation: what to show and how to explain it

Sign in as nurse. Open **Evidence**. Walk top to bottom:

1. **The five numbers.** 97.5% agreement with the QA auditor (117 of 120) against 56.7% for the humans; 0 wrongful approvals; 23 of 24 adversarial; 29 of 30 open queue.
2. **By the kind of mistake the human made.** Where humans followed the void memo, 18 of 18 right; outdated version, 14 of 14; client rule missed, 6 of 7. "The copilot is strongest exactly where the humans were weakest, because rule selection is code."
3. **What is measured, and against what.** This table answers "is this agent observability or accuracy?": both, plus safety and robustness. Accuracy is against the auditor's `qa_correct_decision`; governing source against `qa_governing_sources`; safety is wrongful approvals and tool denials, both zero; robustness is planted text, missing fields, wrong dates, retired versions; consistency is repeat runs; observability is the per-run trace.
4. **Confusion matrix and the three misses.** All three misses sent the case to a person: pend or physician. None approved something that should have been denied.
5. **Run trace.** Pick a case. Show the plan the model wrote, the sections it asked to read, the safety-net reads code added, the search, the verifier result, the second check, tokens and latency. "This is stored with every review. It is what Riverbend can ask for under addendum section 5."
6. **Adversarial table and open queue table.** Scroll; do not read them out.

If asked how the evaluation was run: `scripts/run_eval.py` replays the 120 audited cases through the same pipeline with the auditor's labels hidden, then compares; `scripts/run_open.py` replays the 30 open cases against an answer key I wrote from the policies before running the model. Results are in `data/results/`.

If asked what you would add: a fresh random audit sample nobody has looked at; repeat-run agreement as a monthly QA metric; nurse agreement in shadow mode with every disagreement reviewed.

---

## 6. Cost and business case

Every number here is either from the data pack (financials, roster, addendum, time-and-motion study, call log) or marked (A) as my assumption. Say so when you present it.

**What it costs**

| Item | Year 1 | Ongoing per year |
|---|---|---|
| 90-day build: an FDE, two engineers, half a clinical SME, a security review (A) | $0.30M | |
| Model and fax reading: 310,000 cases at about $0.003, 143,000 faxes at about $0.004 | $0.01M | $0.01M |
| Azure hosting, Postgres, logging, monitoring (A) | $0.05M | $0.06M |
| Support: half an engineer plus half a policy librarian who owns the registry (A) | $0.12M | $0.24M |
| Contingency 15% (A) | $0.07M | |
| **Total** | **about $0.55M** | **about $0.30M** |

That is 0.5% of FY2026 revenue ($112.4M) and one tenth of the hiring plan.

**What it is worth, per year**

| Benefit | Value | Basis |
|---|---|---|
| Service credits avoided | $1.9M | FY2026 forecast line in the financials. The addendum charges 4% of quarterly Riverbend fees per point of timeliness below 97%; at about 90% that is 7 points. Each point is worth about $0.27M a year. Credits are 1.7 margin points and 21% of FY2026 operating profit. |
| Hiring avoided | $2.2M (A) | The VP wants 20 nurses; at $110k loaded (A) that is $2.2M a year. The time-and-motion study puts 14.2 of 38 minutes per case on finding the rule: 37% of nurse time, about 18.9 of 50.6 FTE. The resolver removes most of it; even half fills the 7.4 FTE gap between the 58 budgeted and 50.6 actual. |
| Call-centre capacity | about 12.5 FTE | 2,400 calls a day; 67% are status checks or fax-receipt confirmations (call log); half deflected by the portal and status desk (A); 446 seconds average handle time (call log). About 100 agent-hours a day. Worth about $0.75M a year at $60k loaded (A) if converted; counted as capacity, not savings, in the base case. |
| Intake keying | about 4 FTE | 640 faxes a day keyed into 14 fields; fields confirmed instead of typed (A: 5 minutes a fax, 60% saved). Capacity, not savings. |
| Revenue protected | $6.8M Riverbend; $8.1M Harlan; $42M across 14 employers renewing 1 Jan 2027 | Riverbend PMPM fees are $6.16M (92,400 × $4.10 and 61,300 × $2.20, times 12) plus per-case fees; the credits formula implies about $6.8M of fees. Harlan: 18,400 employees × $36.50 × 12. Not counted in the margin scenarios. |

**Margin forecast** (revenue held at the FY2026 forecast, SG&A flat, no growth counted)

| Scenario | Revenue | Costs | Operating profit | Margin |
|---|---|---|---|---|
| FY2026 forecast (actual trend 14.0% → 11.6% → 9.4% → 8.0%) | $112.4M | $103.4M | $9.0M | 8.0% |
| Hire 20 nurses, credits continue (the VP's plan) | $112.4M | $105.6M | $6.8M | 6.0% |
| Same, and Riverbend leaves on 31 December (A: $6.8M of UM fees lost, credits stop) | $105.6M | $103.7M | $1.9M | 1.8% |
| Copilot, FY2027: credits fall to $0.5M by mid-year (A), year-one cost $0.55M | $112.4M | $102.5M | $9.9M | 8.8% |
| Copilot, FY2028 steady state: credits zero, $0.30M a year | $112.4M | $101.8M | $10.6M | 9.4% |
| Same, with freed call-centre and intake capacity converted to cost (A: $1.0M) | $112.4M | $100.8M | $11.6M | 10.3% |

Payback: year-one cost of $0.55M against $1.4M of credits avoided in FY2027 is about five months. Against the hiring plan the copilot is $1.9M a year cheaper, every year.

The one-line version: the credits are a fifth of operating profit; the copilot costs 0.3 margin points a year and removes the cause; the hiring plan costs 2 points and removes nothing.

**Q: How confident are you in these numbers?**
The revenue, cost, credit, fee and headcount figures are from the pack. The solution cost, the loaded cost per nurse, the deflection rate and the Riverbend share of UM fees are my assumptions and are marked. The margin scenarios hold revenue flat, so they understate the copilot case if the CEO's three further delegated plans happen, and overstate the VP case if Harlan also leaves. I would validate the build cost with Finance and the nurse cost with HR before the board sees it.

**Q: Why not just hire the 20 nurses?**
Because the data says they would not fix either cause. Timeliness did not move with headcount; the misses are incomplete requests, and the errors are rule lookups. Twenty nurses cost 2 margin points a year and leave the $1.9M of credits in place. The copilot costs 0.3 points, removes the rule hunt that is 37% of nurse time, and fills the vacancy gap without a hire.

**Q: What does production actually cost to run?**
About $0.30M a year: mostly people (half an engineer, half a policy librarian), about $60k of Azure, and about $10k of model calls. The model is the cheapest line: a third of a cent per case.

## 7. Who may do what, and why

| Role | Raises requests | Runs the review | Decides | Sees |
|---|---|---|---|---|
| Provider office | Yes, own patients, by form or fax upload | No | No | Status of own requests, notices, coverage check |
| Intake coordinator | Yes, from the fax share, phone and mail | Yes | Pend, route | Full case |
| Nurse reviewer | No | Yes | Approve, pend, route | Full case |
| Physician reviewer | No | Yes | Approve, pend, deny | Full case |
| Member services agent | No | No | No | Status after verifying request number and date of birth; coverage check |
| Auditor | No | No | No | Everything, read only |

Why nurses do not raise cases: the person who decides must not create the record. Receipt time and request content stay independent of the reviewer, which is the first thing an auditor checks, and it keeps the receipt clock honest. Intake and providers raise; reviewers decide; the server enforces it on every request, not only in the interface.

How a request moves: receipt (provider or intake; number, clock, intake check and plan pre-check at once) → review (intake or nurse runs the copilot on demand) → decision (nurse, or physician for anything adverse) → notice (letter generated from the decision; provider sees it in the portal; callers get status from the desk).

---

## 8. Question bank

### Diagnosis

**Why not staffing?** Headcount fell from 57.7 to 50.6 FTE while on-time stayed flat, correlation about -0.05. Timeliness was already below standard when staffing was near budget. Every missed Medicare deadline arrived incomplete; nurse review took about 40 hours whether the case was late or not. Twenty nurses would cost about $2.2M a year and move neither cause. The 14.2 minutes per case spent finding the rule is 18.9 nurses' worth of time, and that is what the copilot removes.

**Is the QA sample representative?** The pack does not say it is random, and it may be enriched for errors, so I do not extrapolate 56.7% to all decisions. The mix of errors still holds, and the direction is confirmed by the appeals data: wrong-version denials overturned 91% of the time.

**Why is "wrong rulebook" the root cause rather than training?** Because the same nurse gets it right when the right document is in front of her. The senior nurse said the clinical part is easy and the hard part is which rules apply. A memo, a stale PACE screen and an email amendment that never reached UM are system failures, not skill failures.

### Build

**Why Agentic RAG and not a rules engine or a plain RAG?** Which document governs is a rules question, so that is code. Whether the record meets the criteria is a reading question across different note styles, so that is a model, bounded to the governing set and verified by code. Plain RAG retrieves a right-looking chunk from the wrong version; an unbounded agent can talk itself into anything. This is the middle.

**Why Gemini Flash?** Cost, speed and image reading: about six seconds and a third of a cent per case. One environment variable switches provider; in production it is whatever Bellcourt's Azure tenant covers under its patient-data agreement.

**Vector database?** Section-level embeddings fused with keyword rank, filtered by the registry, stored in a JSON file because the corpus is 38 documents and 322 sections. At 1,100 documents, Azure AI Search or Pinecone with the same metadata filters; it is one function to swap.

**How is the fax read?** A vision model transcribes the image into fields and returns empty strings for blanks, and separately reports any sentence that tries to instruct the reviewer. Code then validates: member ID against eligibility, service against the list, dates parsed. Not a template parser, because providers send different forms.

**What is the coverage check, and is it the model?** No model. Eligibility file, plan document provisions that mention the service classified as exclusion, condition, limit or amendment with its effective date, the policy version in force on the date of service, its documentation section, and the decision clock. It is the same resolver the review uses, exposed before filing.

**What happens when a policy changes?** The registry is the control: a new version is a new row with effective dates; the old one stays, marked retired, so historical dates still resolve. Make the registry entry part of the Clinical Policy Committee's release step; account managers file plan amendments there, copying UM Operations, which is what failed with Kestrel.

**Scale?** 310,000 a year is about 1,200 a day. At six seconds a case one worker handles it; the serverless functions scale horizontally. About $4 a day in model cost at today's price.

**Determinism?** Temperature 0, but the model still varies. Across runs the open queue scored 27 to 29 of 30, every miss conservative. Add repeat-run agreement to monthly QA and route disagreements to manual review.

**Did you overfit?** Partly, and I say so. I read the QA file while writing the prompt rules. The open queue was an independent check with my own key. Next test: a fresh random sample nobody has seen.

### Governance, security, compliance

**Can it deny?** No. The outcome schema has no deny value; the verifier rejects anything else; letters are generated only from a human decision. The governance page submits a DENY and shows the rejection.

**The Riverbend addendum?** 60 days' notice before use: day 1 of the plan. No automated denial, delay or modification: no deny path, drafts only. Inputs and outputs on audit: stored per run. Arizona-licensed director signs denials: routed by member state and stated in the letter. Texas disclosure: in the letter.

**PHI?** Name, date of birth, phone, record number and member ID removed before the review step; age passed as a fact. The fax-reading step sees the image, so in production it runs inside the BAA tenant. Fax images are served only to signed-in users. Nothing is used for model training.

**Prompt injection?** Provider text is data. Sentences that direct the reviewer are flagged, shown to the human, and barred as evidence. Ten of ten planted instructions ignored in evaluation.

**Who built the roles, and why can't a nurse raise a case?** Segregation of duties: the person who decides does not create the record. Intake and providers raise; reviewers decide; auditors read. Enforced on the server for every request.

**Where would this run?** Bellcourt's Azure tenant under the existing HIPAA BAA, behind Entra ID with the same roles, read-only against the PACE replica, the fax share and the portal webhook. Nothing is written to PACE.

### Evaluation

**Accuracy or observability?** Both, and safety. Accuracy against the auditor's labels; governing source against the auditor's citations; safety as wrongful approvals and tool denials; robustness on hostile inputs; consistency across runs; observability as the stored per-run trace.

**False positives and negatives?** Wrongful approvals: zero of 120. Wrongful adverse routings: three, all to a person as pend or physician review, never a denial. The system fails toward a person.

**How do you measure "governing source correct"?** The auditor records document and section. I compare document ID and version exactly and section by prefix: 118 of 120.

### You

**What did you learn?** That the hard part of prior authorization is not medicine, it is governance: which document wins, and as of when. The senior nurse said it in her interview and the data agreed with her.

**What would you do with another week?** A fresh held-out audit sample; the other 32 plan documents; single sign-on; a proper database-backed audit table; a stronger model on the review step if the sample shows drift.

---

## 9. Do not

- Do not say "AI decides" or "automates denials". Say "recommends", "a person decides".
- Do not read the slides. Each slide has one sentence as its title; say that sentence and one example.
- Do not type a password on a shared screen. Windows are signed in beforehand.
- Do not claim 97.5% as production accuracy. It is agreement with the auditor on a sample that may not be random.
- Do not go past 8:00. Stop mid-sentence if needed and say "and I will leave it there for questions".

## 10. Checklist, 15 minutes before

- Deck open, full screen, slide 1.
- Three windows signed in: provider, intake, nurse. Physician password ready for the optional step.
- Sidebar shows Model live, Supabase, Email on.
- Supabase table cleaned if you want an untouched queue.
- Timer visible to you. Water.
