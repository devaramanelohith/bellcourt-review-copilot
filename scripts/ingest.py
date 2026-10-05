"""Build the knowledge base: 38 PDFs -> sections + metadata registry + embeddings.  Run:  python scripts/ingest.py
Needs pdfplumber (dev only). Output is committed, so the deployed app needs no PDF library."""
import os, re, json, glob, sys
import pdfplumber
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
KB = os.path.join(ROOT, "data", "kb")

# What a PDF header cannot tell us: authority rank (GOV-01), which client a plan belongs to, what a memo relates to.
OVERLAY = {
 "REG-01": dict(doc_type="regulation", rank=1, products=["MA"], title="CMS prior authorization rule (CMS-0057-F)"),
 "REG-02": dict(doc_type="regulation", rank=1, products=["MA", "ACA"], title="State laws on AI in utilization review"),
 "REG-03": dict(doc_type="regulation", rank=1, products=["SELF_FUNDED"], title="ERISA and self-funded plans"),
 "REG-04": dict(doc_type="context", rank=None, products=[], title="Industry context 2026"),
 "RIVERBEND-ADDENDUM": dict(doc_type="delegation_agreement", rank=2, clients=["RB-MA", "RB-ACA"], title="Riverbend UM delegation addendum", effective_from="2026-01-01"),
 "GOV-01": dict(doc_type="governance", rank=0, title="Clinical policy governance (hierarchy of authority)"),
 "UM-MEMO-2025-19": dict(doc_type="memo", rank=4, relates_to=["MP-101"], title="Memo: keep 6-week rule for lumbar MRI"),
 "UM-MEMO-2026-04": dict(doc_type="memo", rank=4, relates_to=["MP-101", "MP-102", "MP-103", "MP-106", "MP-110"], title="Memo: PACE criteria screen schedule"),
 "EMAIL-Kestrel-Amendment": dict(doc_type="email", rank=4, relates_to=["SPD-KESTREL"], title="Email: Kestrel plan amendment"),
}
def clean(page_text):
    out = []
    for ln in page_text.split("\n"):
        s = ln.strip()
        if not s or s.startswith("Bellcourt Health Administrators - fictional company"): continue
        if re.match(r"^(BELLCOURT MEDICAL POLICY MP-\d+ v\d|SPD-[A-Z]+ \| |RIVERBEND-ADDENDUM \| |REG-\d+ \| |GOV-01 \| |UM-MEMO-[\d-]+$|EMAIL \| )", s): continue
        if s == "Section Item Provision": continue
        out.append(s.replace("(cid:127)", "-"))
    return out
def split_sections(lines):
    secs = []; cur = {"section": "0", "title": "Header", "lines": []}
    for ln in lines:
        m = re.match(r"^(\d+)\. ([A-Z].*)$", ln) or re.match(r"^(\d+\.\d+) ([A-Z].*)$", ln)
        if m and len(m.group(1)) <= 4:
            secs.append(cur); cur = {"section": m.group(1), "title": m.group(2)[:70], "lines": [ln]}
        else: cur["lines"].append(ln)
    secs.append(cur)
    return [{"section": s["section"], "title": s["title"], "text": "\n".join(s["lines"])} for s in secs if s["lines"]]

registry, sections = [], []
for path in sorted(glob.glob(KB + "/**/*.pdf", recursive=True)):
    name = os.path.basename(path)[:-4]
    with pdfplumber.open(path) as pdf: lines = [l for p in pdf.pages for l in clean(p.extract_text() or "")]
    flat = re.sub(r"\s+", " ", " ".join(lines))
    doc = dict(file=os.path.relpath(path, ROOT), version=None, effective_from=None, effective_to=None, service_code=None, status="ACTIVE")
    if name.startswith("MP-"):
        doc_id, ver = name.split("_")
        m = re.search(r"Effective for dates of service (\d{4}-\d{2}-\d{2}) (?:through (\d{4}-\d{2}-\d{2})|until superseded)", flat)
        code = re.search(r"Service code\(s\) (BHA-[A-Z]+-\d+|\(applies across services\))", flat).group(1)
        title = re.search(rf"{doc_id}: (.+?) Bellcourt Medical Policy", flat).group(1)
        doc.update(doc_id=doc_id, version=ver, doc_type="policy", rank=3, title=title, effective_from=m.group(1), effective_to=m.group(2),
                   service_code=None if code.startswith("(") else code, status="RETIRED" if "Status: RETIRED" in flat else "ACTIVE")
    elif name.startswith("SPD-"):
        doc.update(doc_id=name, doc_type="plan_document", rank=2, clients=[name[4:]], title=flat.split(" Summary Plan Description")[0][:80])
    else:
        doc_id = re.sub(r"_.*", "", name) if name.startswith("REG-") or name.startswith("GOV-") else name
        doc.update(doc_id=doc_id, **OVERLAY[doc_id])
    registry.append(doc)
    for s in split_sections(lines):
        sections.append(dict(doc_id=doc["doc_id"], version=doc["version"], **s))

json.dump(registry, open(os.path.join(ROOT, "data", "registry.json"), "w"), indent=1)
json.dump(sections, open(os.path.join(ROOT, "data", "sections.json"), "w"), indent=1)
print(len(registry), "documents,", len(sections), "sections")
if "--no-embed" not in sys.argv:
    from copilot import llm
    vecs = []
    for i in range(0, len(sections), 64):
        batch = sections[i:i + 64]
        vecs += llm.embed([f"{s['doc_id']} {s['version'] or ''} section {s['section']} {s['title']}\n{s['text']}"[:6000] for s in batch])
    json.dump([[round(x, 5) for x in v] for v in vecs], open(os.path.join(ROOT, "data", "vectors.json"), "w"))
    print("embedded", len(vecs), "sections")
