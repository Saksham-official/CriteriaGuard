# [CriteriaLens] Approval Checkpoints: Interactive procurement officer interface to review & edit criteria

## 🎯 Overview
Under Indian public procurement regulations (GFR 2017 Rule 144/173 and Central Vigilance Commission guidelines), AI cannot operate as an unverified black box. 

CriteriaGuard implements a **Human-in-the-Loop (HITL) Governance Checkpoint**:
After CriteriaLens extracts eligibility mandates from the tender document, procurement officers must have a dedicated, transparent interface to inspect, calibrate, edit, add, or reject criteria **before any bidder submissions are processed**. 

Once the officer confirms the baseline, the criteria set is locked and signed into the tamper-evident audit trail, unlocking Stage 2 (Bidder Processing).

---

## 🔍 Current State
- A prototype interface exists in `frontend/src/pages/CriteriaReview.jsx` with basic patch/delete capabilities.
- However:
  - There is no enforced tender-level state machine gating bidder processing (`DRAFT` -> `OFFICER_REVIEW` -> `CRITERIA_APPROVED`).
  - Batch approval ("Approve All Verified Criteria") is missing.
  - Officer modifications do not produce an immutable diff in the SHA-256 audit log.
  - The UI lacks visual distinction between AI-extracted values and human-modified overrides.

---

## 🛠️ Required Tasks & Implementation Scope

### 1. State Machine & API Enforcement (`backend/routers/`)
- Enforce tender status progression in `backend/routers/tenders.py`:
  - `EXTRACTION_IN_PROGRESS` -> `PENDING_OFFICER_REVIEW` -> `CRITERIA_APPROVED`.
- In `backend/routers/bidders.py`, verify that a tender has `CRITERIA_APPROVED` status before allowing batch bidder evaluation.
- Add bulk approval endpoint:
  - `POST /api/tenders/{tender_id}/criteria/approve-all`
- Ensure every officer edit or approval records an event to `AuditLog` with:
  - `officer_id`, `action: "CRITERION_EDITED" | "CRITERIA_APPROVED"`, `timestamp`, and previous vs new value diff.

### 2. Frontend Officer Review Interface (`frontend/src/pages/CriteriaReview.jsx`)
- **Status Banner**: Clearly display the tender review status (`Pending Review` vs `Approved & Locked`).
- **Linguistic / Ambiguity Highlights**: Highlight criteria flagged as `ambiguous` with warning pills and explanation tooltips.
- **Inline Editing & Manual Addition**:
  - Modal or inline form allowing the officer to adjust mandatory status, threshold numbers, and evidence documents.
  - Visual tag: `🤖 AI-Extracted` vs `✏️ Officer-Modified`.
- **Add Missing Criterion**: Allow officers to manually add a clause that was omitted by the extraction engine.
- **Lock & Approve Button**: Prominent action button with confirmation modal requiring officer sign-off before proceeding to Bidder Upload.

### 3. Audit Trail Integration
- Connect officer approval actions to the SHA-256 tamper-evident log in `backend/routers/audit.py` so the approval hash is traceable in the final generated PDF report.

### 4. Integration Tests
- Write test in `backend/tests/test_criteria_approval.py`:
  - Verify that bidder evaluation is rejected when status is `PENDING_OFFICER_REVIEW`.
  - Verify that approving criteria transitions tender status to `CRITERIA_APPROVED`.
  - Verify that audit log records officer approval event.

---

## 📋 Acceptance Criteria
- [ ] Officer can review, edit, delete, and add criteria in the UI.
- [ ] Tender status must be `CRITERIA_APPROVED` before bidder evaluations can run.
- [ ] Officer edits and approvals produce SHA-256 chained audit trail records.
- [ ] Polished, responsive UI with clear governance status indicators.

---

## 💡 Contributor Guidance
- **Prerequisites**: React 18, Vite, Tailwind CSS, FastAPI, Python 3.11.
- **Key Files**:
  - `frontend/src/pages/CriteriaReview.jsx`
  - `backend/routers/tenders.py`
  - `backend/routers/bidders.py`
  - `backend/routers/audit.py`
  - `backend/tests/test_criteria_approval.py` (New)
- **Branch Naming**: `feat/criterialens-approval-checkpoints`
- Please refer to [CONTRIBUTING.md](../../CONTRIBUTING.md) for local environment setup instructions.
