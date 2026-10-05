# Submission-ready text

## Comment to post

```
## 📥 Submission: Lohith Devaramane

- 🐙 **GitHub:** @devaramanelohith · 🎓 **Cohort:** [C2]
- 🔗 **Submission:** https://github.com/devaramanelohith/bellcourt-review-copilot
- ▶️ **Demo:** https://bellcourt-review-copilot.vercel.app (sign-in required; demo logins: [paste from DEMO_LOGINS.txt]) · video: [your recording link]
- 🔍 **Problems I found:** (1) Reviewers apply the wrong rule: 34% of 2026 denials cite a retired policy version and 91% of those are overturned. (2) The clock is lost at intake: 66 of 69 late decisions arrived incomplete, and faxes wait 17 hours before keying. (3) No status visibility: 67% of calls ask where a request is.
- 🎯 **What I built:** Wrong-rule decisions and late detection of incomplete requests, solved using Agentic RAG with a deterministic rule resolver and a human decision at the end, built with Python (standard library), Gemini 2.5 Flash via OpenRouter, a metadata registry plus vector index, and Vercel. On Bellcourt's 120 audited cases it agrees with the auditor on 117 (97.5%) against 68 (56.7%) for the original human decisions, with zero wrongful approvals.
```

## Deliverables checklist

| Deliverable | File or link |
|---|---|
| Documentation (PDF, max 8 pages) | `docs/Bellcourt_Case_Documentation.pdf` |
| Architecture diagram | `docs/Architecture_Diagram.pdf`, `docs/architecture.png`, mermaid in `README.md` |
| Implementation strategy (90 days) + one-page design note | `docs/Implementation_Strategy_and_Design_Note.pdf` |
| Working demo | https://bellcourt-review-copilot.vercel.app |
| README + setup steps | `README.md` |
| Evidence it works | `docs/EVIDENCE.md`, Evidence tab in the app, `tests/` |
| Pitch deck (optional, 14 slides) | `docs/Pitch_Deck.pdf` |

## One-line answers for the panel

- **Problem:** Bellcourt is late because requests arrive incomplete, and wrong because reviewers cannot find the governing rule.
- **How I found it:** tested each stakeholder claim against the request file, the QA audit, staffing and call logs. Staffing does not explain the misses.
- **Approach and why:** Agentic RAG. Plain RAG would retrieve the retired version; an autonomous agent is not allowed to decide. Code selects the rules, the model reads and checks, a person decides.
- **Architecture:** intake, member and clock, rule resolver, review agent, verifier, reviewer screen, audit log. Read-only beside PACE.
- **Live demo:** cases 8113, 8100, 8106, 8120, 8105, then New request with two dates, then Evidence.
