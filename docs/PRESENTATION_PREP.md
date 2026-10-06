# Presentation prep: Bellcourt case study

Evaluator: Sumit Shukla (data scientist, FDE Academy). His required flow: problem and how you discovered it, then the demo, then the technical side (key elements, governance, security, evaluation). 8 minutes to present, 2 for questions. Claims must trace to the data pack.

Your single sentence: **"Bellcourt is late because requests arrive incomplete and wrong because reviewers cannot find the rule that governs. I built a copilot where code picks the rule, the model checks the evidence, and a person decides."**

---

## 1. The 8-minute flow Sumit asked for

His instruction, from the voice message: problem and how you discovered it, then straight into the demo, then the technical side: key elements, governance, security, evaluation. Eight minutes to present, two for questions. Do not run over.

Use the short deck `Pitch_Deck_8min.pdf` (6 slides). Slides 1 and 2 before the demo, slides 3 to 6 after it.

| Minute | Part | Say this, in your own words |
|---|---|---|
| 0:00 to 0:45 | Slide 1: the problem | "Bellcourt is a TPA. It runs health plans for 38 employers and decides prior authorization requests for an insurer, Riverbend. Riverbend is penalising them, $1.9M this year, and may leave in December. Decisions are late, 90% on time against 97, and wrong: 57% correct in their own QA audit against 95. Leadership blames nurse headcount." |
| 0:45 to 2:00 | Slide 2: how I found it | "I tested that claim against their data. Headcount fell from 57.7 to 50.6, but timeliness was already failing at full staffing and didn't track headcount. The decisive cut: every one of the 64 late Medicare Advantage decisions arrived incomplete; complete requests are on time 99.8% of the time. So lateness is an intake problem. And accuracy: 39 of 52 audited errors are rule lookups, not clinical judgement. A third of 2026 denials cite a retired policy version; those are overturned 91% of the time. A memo told nurses to keep a 6-week rule after the policy moved to 4 weeks: 72 wrong denials." Then: "Let me show you what I built." |
| 2:00 to 5:30 | Demo, live | Follow Section 2. Queue, case 8100, upload fax 8120 and run it, approve 8100 and open the letter, physician denial on 8105. Keep moving. |
| 5:30 to 6:30 | Slide 3: key elements | "Six elements. A metadata registry of all 38 documents with effective dates and authority rank. A rule resolver in code that picks what is in force; the model never chooses a version. A bounded agent that plans its reads, uses a read tool that refuses anything not in force, and quotes its evidence. A verifier in code: citations in force, quotes in the record, outcome consistent, visit arithmetic recomputed. A second skeptical pass on approvals. A human decision with no deny outcome, and a letter generated from that decision." |
| 6:30 to 7:15 | Slide 4: governance and security | "Governance: GOV-01's hierarchy is enforced in code, memos can never be criteria, every run stores inputs, documents, versions, tool trace, output and the human decision, which is what the Riverbend addendum requires on audit. Only physicians can deny, enforced on the server. Security: sign-in with hashed passwords and signed sessions, roles on the server, data and fax images served only to signed-in users, identifiers stripped before the model sees the record, provider text treated as data with planted instructions flagged. Production runs in the Azure tenant that already has the patient-data agreement, after the 60-day notice to Riverbend." |
| 7:15 to 8:00 | Slide 5: evaluation | "Tested on Bellcourt's own 120 audited cases: 117 agree with the auditor, the humans scored 68, zero wrongful approvals. On the cases humans got wrong for a rule reason, 38 of 39. Ten planted instructions, all ignored. Seven time-travel cases: the version flips with the date. 36 unit tests with no model. Limits: results vary a little between runs, always toward a person, and I tuned on these cases, so a fresh audit sample is the next test." Slide 6 stays on screen for questions. |

If you are at 7 minutes and still in the demo, skip the physician step and go to slide 5. Evaluation is the slide he asked for by name.

## 2. Demo script (3.5 minutes, inside the 8)

Before the session: sign in as nurse in one window and as physician in a private window. Have `data/fax/FAX-PA-2609-8120.png` in a Finder window. Clean the Supabase table if you want an untouched queue.

1. **Queue (20 sec).** "Five sample cases sorted by time left. 8113 is a fax marked urgent, already overdue, and nobody had typed it in."
2. **Case 8100 (60 sec).** "Lumbar MRI, 5 weeks of therapy. The memo and the screen say 6 weeks. The copilot picked version 2 by date of service, and lists version 1 and the memo as deliberately not used, with the reason." Point at one Met criterion with its quote. Click Read on MP-101 v2 once: "every citation opens the source."
3. **Upload fax 8120 (70 sec).** New case, upload, run review. "A vision model read the form. Juniper's plan requires a second opinion; it is not in the record, so: need information, and the request to the provider is already drafted. And this flag: the fax says Juniper dropped that rule and asks us to approve today. Flagged as a planted instruction, ignored."
4. **Approve and letter (40 sec).** Back on 8100, Approve. Decision letters: "generated from my decision, cites the section, PDF, email."
5. **Physician (30 sec).** Private window, 8105: "the nurse could not deny this. The physician can, and the letter carries the reason, appeal rights and the Arizona sign-off."

If anything fails live: "the saved results are in the Evidence tab", and move on. Never debug on stage.

## 3. Numbers to know cold

| Number | Meaning | Source file |
|---|---|---|
| 38 employers, 453,000 lives; Riverbend 92,400 MA + 61,300 Marketplace | Customers | company_fact_sheet, client_roster |
| 310,000 requests a year; fax 46%, portal 31%, phone 15%, electronic 8% | Volume and channels | process document |
| Margin 14.0% to 8.0%; revenue +9.3%, clinical cost +27.7% | Money | financials CSV |
| $1.9M service credits; 4% of quarterly fees per point below 97% | Penalty mechanics | financials; addendum s6 |
| 90.1% on time (Q2 2026) vs 97%; 87.0% in Q1 2025 | Timeliness | pa_requests |
| 66 of 69 late arrived incomplete; complete on time 99.8% | Intake is the cause | pa_requests |
| Late cases: 122 of 199 hours waiting for information | Where time goes | pa_requests |
| Nurse FTE 57.7 to 50.6; correlation with on-time -0.05 | Staffing | nurse_staffing_weekly |
| QA accuracy 68 of 120 (56.7%); 39 of 52 errors are wrong-rule | Accuracy | qa_audit_sample |
| 34% of 2026 denials cite a retired version; overturned 91% | Root cause 1 | pa_requests |
| 72 MRI denials under the memo; 18 of 21 appeals overturned | Memo | pa_requests, UM-MEMO-2025-19 |
| 14.2 of 38 minutes finding rules = 18.9 of 50.6 FTE | Capacity | time study in process doc |
| 57% status calls, 20% abandoned | Visibility | call_center_log |
| 117 of 120; 0 wrongful approvals; 29 of 30; 23 of 24; 36 tests | My results | docs/EVIDENCE.md |
| About 6 seconds and a third of a cent per case | Cost | eval.json |

## 4. Questions he is likely to ask, and answers

### About the business and diagnosis

**Q: Explain Bellcourt's business to me like I know nothing.**
Employers who pay their own medical bills hire Bellcourt to run the plan. Bellcourt pays claims, keeps the member list, and checks expensive treatments before they happen. It is paid a fixed fee per employee per month. Separately, an insurer, Riverbend, pays Bellcourt to do that checking for its members, and penalises lateness and errors.

**Q: Why is the margin falling?**
Costs grew twice as fast as revenue. Clinical staff up 28%, intake and call centre up 24%, revenue up 9%. On top of that, $1.9M of penalties this year. The cost growth comes from slow manual work: retyping faxes, hunting for rules, rework after wrong denials, and phone calls asking for status.

**Q: The VP says staffing. Why is he wrong?**
Three facts. Timeliness was already failing at full staffing. The weekly on-time rate does not track headcount. And every single late Medicare Advantage decision arrived incomplete. He is right that the nurse stage got slower as people left, so staffing is a real strain, but it is not why deadlines are missed.

**Q: How do you know the QA sample is representative?**
I don't, and I say so. The pack does not say how the 120 cases were chosen, so I never extrapolate 56.7% to all decisions. What I do have independently is the full request file: a third of 2026 denials cite a retired version, and appeals on those are overturned 91% of the time. Two different files, same story.

**Q: Correlation isn't causation. What about the staffing claim?**
Agreed, which is why I didn't rely on the correlation alone. The decisive evidence is deterministic: 100% of late MA standard cases were incomplete on receipt and 0% of complete ones were late. That is not a correlation, it is a partition.

**Q: Why rank wrong-rule above intake when intake causes the penalties?**
Because fixing speed alone delivers wrong decisions faster, and accuracy below 95% triggers the Corrective Action Plan on its own. The CEO asked for faster and more defensible. Also the rule engine is the foundation for the intake fix, so I built the intake slice on top of it.

### About the approach

**Q: Why Agentic RAG and not plain RAG?**
Plain RAG picks passages by similarity. The retired version of a policy is nearly identical text to the current one, and the memo contradicting the policy is highly relevant to the query. Similarity would surface exactly the wrong documents. The selection has to be by metadata: client, service, date of service, authority rank. That is code. Then the model needs to read several sections, follow references like "see MP-117" or "subject to Section 5.3", and ask for more if needed. That is the agentic part.

**Q: Why not a full AI agent?**
The contract and the state laws forbid any tool from denying, delaying or modifying a request. So the loop is bounded, the outcome set has no denial, and the human decision is the last step.

**Q: Where exactly does the model make decisions, and where does code?**
Code: eligibility, clock, which documents are in force, verification of citations and quotes, arithmetic on visit limits, role permissions, letter generation. Model: reading the fax, deciding which sections to read, judging whether a quote satisfies a criterion, the second skeptical check. Person: the decision.

**Q: What stops the model from citing a retired version?**
Two layers. The read tool refuses any document not in the governing list and says why. The verifier rejects any citation outside that list and sends the answer back. In the test suite there is a case that asks for MP-101 v1 and gets refused.

**Q: What stops hallucinated evidence?**
Every Met or Not met needs a verbatim quote. The verifier checks the quote exists in the record after normalisation. If the record is silent, the only allowed status is Not documented, which leads to a request for information, never a denial.

**Q: Prompt injection?**
Three layers. A regex detector flags instruction-like text. The prompt says text inside the record is data. The verifier refuses a quote drawn from flagged text. And the test proves it: ten planted instructions on cases that should not be approved, outcome unchanged in all ten, plus the two real planted faxes in the pack.

**Q: Why a second model pass on approvals?**
A wrong approval is the error no human will catch, because nobody appeals an approval. The second pass is skeptical by instruction and narrow: it only reports contradictions or missed exclusions. It caught the case where the model read "no radiation below the knee" as radiculopathy.

**Q: Why Gemini 2.5 Flash and not Claude or GPT?**
Cost, speed and image reading. Six seconds and a third of a cent per case. I tested Claude Haiku and Sonnet on the hard cases: better on one case, slower, and ten times the cost. The provider is one environment variable; the architecture does not depend on the model. In production this would be whatever Bellcourt's Azure tenant covers under its patient-data agreement.

**Q: Embeddings? Vector database?**
Section-level embeddings, 256 dimensions, fused with keyword rank, filtered by the registry. Stored in a JSON file because the corpus is 38 documents and 322 sections; a hosted vector database adds a key and a failure point with no retrieval gain at this size. At 1,100 documents I would use Azure AI Search or Pinecone with the same metadata filters, and it is one function to swap.

**Q: Determinism? You ran it twice and got different answers.**
Yes. Temperature 0 but the model still varies. Across runs the open queue scored 27 to 29 of 30, and every miss was conservative: manual review, need information, or physician referral, never a wrongful approval. For production I would add a repeat-run agreement metric to the monthly QA and route disagreements to manual review.

**Q: Did you overfit the prompts to the test set?**
Partly, and I say so in the evidence. I read the QA file while writing the prompt rules, for example that a request exceeding the visit limit is "not covered". The open queue was an independent check with my own answer key. The honest next step is a fresh random audit sample that nobody looked at.

**Q: How do you measure "governing source correct"?**
The auditor records the governing document and section for each case. I compare document ID and version exactly, and section by prefix. 118 of 120.

**Q: What is your false positive and false negative?**
Frame it as the two errors that matter. Wrongful approvals: zero of 120. Wrongful adverse routings: three cases, all of which went to a human as manual review or physician referral rather than a denial. The system is built to fail toward a person.

### About the build and production

**Q: How does the fax get read? OCR?**
A vision model transcribes the image into fields and returns empty strings for blanks. Not a template parser, because providers send different forms. Then code validates: member ID against the eligibility file, service name against the list, dates parsed. PDFs are rendered to an image in the browser first.

**Q: Phone requests?**
The agent keys them during the call, as today. The tool does not listen to audio. The form shows missing items while the caller is still on the line, which is the real win.

**Q: What about PHI?**
Name, date of birth, phone, record number and member ID are removed before the review step; the model gets a de-identified narrative and an age. The fax reading step necessarily sees the image, so in production that runs inside the tenant covered by the patient-data agreement. Sign-in, roles enforced on the server, audit log.

**Q: How does this fit the Riverbend contract?**
60 days' written notice before use: day 0 of the plan. No automated denial, delay or modification: no deny outcome, drafts only. Inputs and outputs on audit: stored per run. Arizona-licensed director signs denials: routed by member state. Texas disclosure: in the letter.

**Q: What happens when a policy changes?**
The registry is the control. A new version is a new row with effective dates. The old version stays, marked retired, so historical dates of service still resolve correctly. I would make the registry entry part of the Clinical Policy Committee's release step, and have account managers file plan amendments there, copying UM Operations, which is exactly what failed with Kestrel.

**Q: Scale to 310,000 requests a year?**
That is about 1,200 a day. At 6 seconds a case, one worker handles it; the serverless functions scale horizontally anyway. Cost about $4 a day at today's model price. The database and the vector index are the parts that change at scale, and both are behind one interface.

**Q: What would you do with another week?**
A fresh held-out audit sample. A stronger model on the review step if the sample shows drift. The other 32 plan documents. A proper database-backed audit table and single sign-on. Provider-facing status and a requirements assistant, which is problem 3.

**Q: What did not work?**
The first version of the second-check prompt was too pedantic and downgraded correct approvals; I narrowed it to contradictions and missed exclusions. The verifier initially rejected quotes that were stitched from two sentences; I allowed fragment matching. Claude via OpenRouter was better on one hard case but ten times the cost and slower.

### About you

**Q: What did you learn about the domain?**
That the hard part of prior authorization is not medicine, it is governance: which document wins, and as of when. The senior nurse said exactly that in her interview, and the data agreed with her.

**Q: What would you tell the CEO in one sentence?**
Send Riverbend the 60-day notice today, withdraw the memo, fill the seven vacancies, and run the copilot on the employer plans while the notice runs.

## 5. Things not to do

- Do not claim 97.5% as a production accuracy figure. Say "on the 120 audited cases, with the limits I listed".
- Do not say the tool "decides" or "approves". It recommends. Humans approve. Physicians deny.
- Do not say OCR. Say a vision model reads the form and code validates the fields.
- Do not read slides. Say the number, then what it means, then where it came from.
- If asked something you do not know, say "I did not test that" and say how you would.
- Do not debug on stage. Fall back to the Evidence tab.

## 6. Tonight and tomorrow

- Read the documentation PDF once and the numbers table above twice.
- Rehearse the demo once end to end with a timer. Delete the test rows in Supabase first if you want a clean queue.
- Sleep. The material is ready; a rested presenter beats a prepared one.
- Tomorrow 15 minutes before: open both browser windows, sign in, open the Finder with the two files, open the deck PDF.
