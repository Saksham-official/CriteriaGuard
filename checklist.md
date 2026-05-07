# 🎯 CriteriaGuard: 5-Day Vibe Coding Master Checklist

This checklist is your daily source of truth to ensure all six core demo requirements are met and the project is ready for the hackathon jury[cite: 5]. 

## 🗓️ Day 1: Foundation + Engine 1 (CriteriaLens)
**Goal:** Tender uploaded → criteria extracted and displayed for officer review[cite: 5].

- [x] Set up project structure (frontend + backend folders, GitHub repo, Render deployment)[cite: 5].
- [x] Install dependencies: FastAPI, pdfplumber, PyMuPDF, anthropic, pydantic, supabase-py[cite: 5].
- [x] Build `/api/upload-tender` endpoint: accepts PDF, extracts text with pdfplumber[cite: 5].
- [x] Implement CriteriaLens engine: send extracted text to Claude with the extraction prompt[cite: 5].
- [x] Parse + validate Claude response with Pydantic `CriterionSchema` model[cite: 5].
- [x] Store criteria in SQLite with `tender_id` foreign key[cite: 5].
- [x] Build `CriteriaReview.jsx`: display extracted criteria in editable cards, officer approves each[cite: 5].
- [x] Mark ambiguous mandatory criteria with amber badge — officer must confirm before proceeding[cite: 5].
- [x] Test with 2 real-looking synthetic tender PDFs; fix extraction failures[cite: 5].
- [x] Commit + deploy to Render; confirm live URL works[cite: 5].

---

## 🗓️ Day 2: Engine 2 — Bidder Document Parsing
**Goal:** Any bidder document type → extracted values with source citations[cite: 5].

- [x] Build `/api/upload-bidder` endpoint: accepts multi-file upload per bidder[cite: 5].
- [x] Implement routing logic: if image/scanned JPG/PNG → Google Vision OCR; if typed PDF → pdfplumber[cite: 5].
- [x] Add image preprocessing before OCR: deskew + contrast with Pillow (free, local)[cite: 5].
- [x] Store extracted text per page with metadata: `{doc_name, page_number, ocr_quality, raw_text}`[cite: 5].
- [x] Implement DocProbe engine: for each criterion × bidder, call Claude with value extraction prompt[cite: 5].
- [x] Build source citation store: every extraction saves `{doc_name, page, excerpt, confidence}`[cite: 5].
- [x] If Claude returns `value_found: false`, store explicit 'not found' signal — never invent[cite: 5].
- [x] Test DocProbe with: (a) clean typed PDF, (b) good scan, (c) degraded scan, (d) missing doc[cite: 5].
- [x] Build simple Processing screen in React showing progress per bidder per criterion[cite: 5].
- [x] Confirm Google Vision API is returning results — have Tesseract as local fallback[cite: 5].

---

## 🗓️ Day 3: Engine 3 + Verdict Dashboard
**Goal:** All verdicts computed; dashboard showing Eligible / Not Eligible / Needs Review[cite: 5].

- [x] Implement VerdictCore logic in Python (pure logic, no LLM)[cite: 5].
- [x] Run VerdictCore across all criterion × bidder pairs; store all verdicts with explanations[cite: 5].
- [x] Build `Dashboard.jsx`: bidder summary cards with traffic light status (green/red/amber)[cite: 5].
- [x] Show: total criteria, how many passed/failed/pending per bidder at a glance[cite: 5].
- [x] Build `BidderDetail.jsx`: click any bidder → see criterion-by-criterion verdict table[cite: 5].
- [x] Each criterion row shows: status badge, extracted value, source document, page, plain-English reason[cite: 5].
- [x] Add collapsible source excerpt panel — officer can read the exact text the system cited[cite: 5].
- [x] Build `ReviewQueue.jsx`: all Needs Review cases with full context + Approve/Reject/Request Doc buttons[cite: 5].
- [x] Log every officer decision: `{officer_id, criterion_id, bidder_id, decision, reason, timestamp}`[cite: 5].
- [x] Test the full pipeline end-to-end with all 5 synthetic bidders[cite: 5].

---

## 🗓️ Day 4: Report Generator + Audit Trail
**Goal:** Government-quality PDF report exported; tamper-evident audit trail visible[cite: 5].

- [x] Build `report_gen.py` using WeasyPrint (substituted with xhtml2pdf): HTML template → signed PDF[cite: 5].
- [x] Report structure: cover page (tender name, date, officer name), criteria summary table, per-bidder verdict tables, evidence appendix[cite: 5].
- [x] Style the report to look like a real government procurement document — formal header, MoD/CRPF-style typography, page numbers, signature block[cite: 5].
- [x] Add `/api/export-report` endpoint returning PDF binary[cite: 5].
- [x] Build `AuditTrail.jsx`: timeline of every system action with timestamp, actor, action, outcome[cite: 5].
- [x] Implement SHA-256 chaining: each audit log entry hashes its content + previous hash[cite: 5].
- [x] Display hash on each audit entry — visually demonstrates tamper-evidence to technical jury[cite: 5].
- [x] Add hash verification: system automatically verifies the entire chain on load and displays status[cite: 5].
- [x] Build `/api/audit` endpoint returning full log with verification results[cite: 5].
- [x] Polish all screens: consistent design, loading states, error states, and empty states[cite: 5].

---

## 🗓️ Day 5: Demo Data + Rehearsal + Submission
**Goal:** Demo runs flawlessly 3 times; all deliverables submitted[cite: 5].

- [x] Create the perfect demo dataset (The Mock Tender + 5 Specific Bidders)[cite: 5].
- [x] Pre-cache API results for demo dataset so latency cannot ruin the live demo[cite: 5].
- [ ] Record 5-minute demo video as insurance (upload to YouTube unlisted)[cite: 5].
- [x] Write clean `README.md`: project description, architecture diagram, setup instructions, live URL[cite: 5].
- [x] Create architecture diagram (draw.io free tier)[cite: 5].
- [x] Final UI polish: make the report PDF look genuinely government-issue[cite: 5].
- [ ] Rehearse demo script 3 times — hard cut at 5 minutes, practice this specifically[cite: 5].
- [x] Push final code to GitHub with clean commit history[cite: 5].
- [x] Complete Supabase migration: All tables, RLS policies, and Storage buckets fully configured[cite: 5].
- [ ] Submit: live URL, GitHub repo link, demo video link, sample report PDF[cite: 5].

---

## 📋 Final Submission Deliverables (Priority Order)

- [ ] **Working web prototype with live URL** (Target: Day 1 deploy)[cite: 5].
- [ ] **GitHub repo** — clean README + architecture diagram (Target: Day 5)[cite: 5].
- [ ] **Sample evaluation report PDF** (system-generated) (Target: Day 4)[cite: 5].
- [ ] **5-minute demo video** (YouTube unlisted) (Target: Day 5)[cite: 5].
- [ ] **Architecture diagram** (draw.io PNG exported to repo) (Target: Day 5)[cite: 5].

## 🛡️ The "Must-Have" Feature Checks
- [x] End-to-end test on 5 synthetic bidders completed[cite: 5].
- [x] Audit trail with SHA-256 hashing is clearly visible in the UI[cite: 5].
- [x] Officer review queue is functioning with mandatory reasoning[cite: 5].
- [x] Extraction confidence and review sub-reasons implemented[cite: 5].
- [x] Comparative Bidder Matrix view built[cite: 5].
- [x] Govt-procurement domain knowledge added to AI prompts[cite: 5].
- [x] Real-time evaluation progress with polling implemented[cite: 5].
- [x] Tender Complexity Analyzer card added[cite: 5].
- [ ] Committed code to GitHub *every single day* to prove systematic building[cite: 5].

---
> **Daily Standup Rule:** Run the check-in at the end of every day. If any answer is No, fix it before sleeping — do not carry broken state forward[cite: 5].