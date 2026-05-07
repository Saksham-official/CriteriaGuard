# CriteriaGuard — Winning Prototype Checklist
> Mapped against CRPF Hackathon PS judging criteria. Every item traces back to a scoring dimension.

---

## TIER 1 — Non-Negotiables
> Judges will disqualify if any of these are missing

- [x] **Criterion-level explainability on every verdict**
  Each verdict card shows: criterion text → document used → page number → extracted value → pass/fail reason. Not just a badge — a full evidence trail.

- [x] **No silent disqualification UI**
  Three-state system (`ELIGIBLE` / `NOT_ELIGIBLE` / `NEEDS_REVIEW`) must be visually distinct. Every `NEEDS_REVIEW` must show *why* it was flagged (low OCR confidence, borderline value, or ambiguous language).

- [x] **Scanned document handling demo**
  At least one bidder in your demo data must have a scanned/low-quality document that triggers a `NEEDS_REVIEW` verdict with `ocr_quality: low` shown to the officer.

- [x] **Audit trail visible in UI**
  Live, scrollable log showing every action with timestamp, actor, and the SHA-256 hash chain. A chain integrity check button (`✓ Chain intact`) must be visible and clickable.

- [x] **Consolidated PDF report export**
  One-click report generation showing the full bidder × criteria evaluation matrix with verdicts and evidence citations. Officer signature block included.

---

## TIER 2 — Judge-Impressing Differentiators
> These win the score gap over other teams

- [x] **Officer Review Queue for ambiguous criteria**
  After tender extraction, criteria flagged `mandatory_confidence: ambiguous` appear in amber-bordered review cards. Officer can confirm mandatory/optional *before* evaluation starts. This is the biggest differentiator — most teams won't build this.

- [x] **Override with reason logging**
  Officer can override any `NOT_ELIGIBLE` or `NEEDS_REVIEW` verdict but must type a reason. The override is logged in the audit trail with officer name, timestamp, and reason. Show this working in the demo.

- [x] **Borderline detection callout**
  When a value is within 10% of a threshold (e.g., turnover ₹4.6 Cr vs ₹5 Cr required), flag it as `BORDERLINE` in amber — not just `NOT_ELIGIBLE`. Judges love this nuance.

- [x] **Confidence score breakdown per extraction**
  For each extraction, show the four confidence factors (OCR quality, value alignment, authenticity, parseability) as a mini-breakdown, not just a single number.

- [x] **Document type routing badge**
  During processing, show which pipeline was used: `pdfplumber (digital)` vs `Google Vision OCR (scanned)` vs `Tesseract fallback`. Makes the architecture tangible to judges.

- [x] **Ambiguity resolver helper**
  When an officer clicks on an amber-flagged criterion, show the AI's structured analysis (`likely_mandatory`, `reasoning`, `similar_criterion_pattern`) as a helper panel. Officer still makes the final decision.

---

## TIER 3 — Demo Scenario
> Use the exact sample scenario from the PS — judges wrote it, they'll look for it

**Tender:** Construction services
**Criteria extracted:**
1. Minimum annual turnover of ₹5 crore (financial, mandatory)
2. At least 3 similar projects in last 5 years (technical, mandatory)
3. Valid GST registration (compliance, mandatory)
4. ISO 9001 certification (certification, mandatory)

**10 Bidders:**

| # | Bidder | Turnover | Projects | GST | ISO | Expected Verdict |
|---|--------|----------|----------|-----|-----|-----------------|
| 1 | Sharma Constructions | ₹8.2 Cr (typed PDF) | 5 | Valid | Valid | ✅ ELIGIBLE |
| 2 | Mehta Builders | ₹6.1 Cr (typed PDF) | 4 | Valid | Valid | ✅ ELIGIBLE |
| 3 | Gupta & Sons | ₹5.5 Cr (typed PDF) | 3 | Valid | Valid | ✅ ELIGIBLE |
| 4 | Rajput Infra | ₹7.0 Cr (typed PDF) | 2 | Valid | Valid | ❌ NOT_ELIGIBLE (projects < 3) |
| 5 | Singh Works | ₹3.8 Cr (typed PDF) | 4 | Valid | Missing | ❌ NOT_ELIGIBLE (turnover + ISO) |
| 6 | Verma Corp | ₹5.1 Cr (typed PDF) | 3 | Valid | Valid | ✅ ELIGIBLE |
| 7 | Kumar Ltd | ₹4.6 Cr (typed PDF) | 4 | Valid | Valid | ⚠️ NEEDS_REVIEW (borderline turnover, within 10%) |
| 8 | Patel Infra | Scanned cert, illegible | 3 | Valid | Valid | ⚠️ NEEDS_REVIEW (OCR failed on turnover figure) |
| 9 | Reddy Build | ₹6.8 Cr (typed PDF) | 3 | Expired | Valid | ❌ NOT_ELIGIBLE (GST expired) |
| 10 | Nair Group | ₹5.9 Cr (typed PDF) | 3 | Valid | Valid | ✅ ELIGIBLE |

> **Result split:** 6 eligible, 3 not eligible, 1 flagged — exactly matching the PS success scenario.

---

## TIER 4 — Screens & Navigation

- [x] **Dashboard / Landing**
  Summary cards: total tenders, active evaluations, pending reviews, completed. Recent activity feed.

- [x] **Tender Upload & Processing**
  Upload UI with animated pipeline progress: `Extract → Validate → Officer Review`.

- [x] **Criteria Review Screen**
  List of all extracted criteria. Amber cards for ambiguous ones. Officer approve/edit flow with inline editing.

- [x] **Bidder Management**
  Upload multiple bidder document sets. Show processing status per bidder with document type routing badge.

- [x] **Evaluation Matrix (Hero Screen)**
  Bidders as rows, criteria as columns, verdict badges in cells. Click any cell to open the Evidence Drawer.

- [x] **Evidence Drawer**
  Slide-out panel showing: extracted value, source document, page number, verbatim 80-word excerpt, confidence breakdown, authenticity score.

- [x] **Review Queue**
  Dedicated screen for all `NEEDS_REVIEW` items sorted by tender. Officer approve/override actions here.

- [x] **Audit Trail Screen**
  Full append-only log. Filter by tender/bidder/action type. Integrity verification button showing hash chain status.

- [x] **Report Preview & Export**
  Formatted evaluation summary. Officer signature block. Export to PDF button.

---

## TIER 5 — Architecture Proof Points
> Judges read your docs AND your UI — these details signal depth

- [x] Show `temperature=0` — mention it explicitly when explaining why results are deterministic (extraction is retrieval, not generation)
- [x] Display `not_found_reason` enum in UI for missing documents: `document_missing | value_unreadable | not_stated`
- [x] Source excerpt displayed verbatim, max 80 words, in a monospace/quote block
- [x] Processing stages use exact engine names: **CriteriaLens**, **DocProbe**, **VerdictCore** — not generic labels
- [x] VerdictCore verdict computation explicitly labelled as "deterministic logic (no LLM)" — this is a key trust signal
- [x] Pydantic validation retry cycle shown: `Attempt 1 → validation fail → Attempt 2 → success / flag low-confidence`

---

## TIER 6 — Polish That Closes the Deal

- [x] Real-time processing simulation with step-by-step progress (even if mocked) — judges need to *feel* the system working
- [x] Consistent color coding throughout: green (ELIGIBLE), red (NOT_ELIGIBLE), amber (NEEDS_REVIEW / BORDERLINE)
- [x] All empty states handled gracefully — no blank pages
- [x] The Evaluation Matrix is the hero screen — make it information-dense and visually impressive
- [x] Desktop-optimised (this is a government procurement tool, not a consumer app)
- [x] Error states shown clearly: `NEEDS_REVIEW` with explicit reason string, never a generic error message
- [x] Mandatory criteria marked with a red `M` badge; optional with a grey `O` badge throughout

---

## Judging Criterion → Feature Mapping

| PS Judging Criterion | Prototype Feature That Covers It |
|----------------------|----------------------------------|
| Clarity of problem understanding | Dashboard framing, officer-centric UX language, CRPF context in UI copy |
| Technical soundness | CriteriaLens/DocProbe/VerdictCore engine labels, confidence breakdown, document routing badge |
| Edge cases: scanned docs, photos, ambiguity | Patel Infra demo bidder (OCR failure), ambiguous criteria amber cards, borderline detection |
| Human-in-the-loop design | Officer Review Queue, override with reason, ambiguity resolver helper |
| Audit trail design | SHA-256 chain visible, append-only log, integrity check button |
| Architecture & tech justification | Evidence drawer shows which model/pipeline was used; deterministic VerdictCore label |
| Risks & trade-offs | NEEDS_REVIEW as explicit state (not silent failure) shows you understand the stakes |

---

## What NOT to Build (Save Time)

- [x] Real OCR processing — pipeline states show output (implemented)
- [x] Actual API calls in the demo — Llama 3.3 via Groq (implemented)
- [x] File format conversion (DOCX → text) — fully supported (implemented)
- ❌ Multi-user auth — one officer role is enough for the prototype
- ❌ Mobile responsiveness — desktop only

---

*Built for CRPF AI-Based Tender Evaluation Hackathon 2026*
