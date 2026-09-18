---
name: '🔍 CriteriaLens (Tender Intelligence) Task'
about: Propose or track an enhancement for Stage 1 Tender Intelligence & CriteriaLens
title: '[CriteriaLens] <Short task description>'
labels: ['enhancement', 'criteria-lens', 'backend']
assignees: ''
---

### 🎯 Scope & Objective
Describe the improvement or new capability for Stage 1 (CriteriaLens):
- [ ] Formal Schema Extraction (Financial, Technical, Compliance mandates)
- [ ] Linguistic Marker Analysis (Deontic modality: "shall", "must" vs "should", "preferred")
- [ ] Approval Checkpoints & Officer Review Interface
- [ ] Multi-page chunking / Table Extraction / OCR fallback

### 📑 Context & Background
Explain the procurement document format or clause pattern this task addresses (e.g. GeM guidelines, CPWD schedules, CVC compliance).

### 🛠️ Technical Plan
- **Files to Modify**: e.g., `backend/engines/criteria_lens.py`, `backend/models/criterion.py`, `frontend/src/pages/CriteriaReview.jsx`
- **Pydantic Schema changes**:
- **Prompt / Parser adjustments**:

### 🧪 Test Cases
- [ ] Test with standard mandatory clauses ("Bidder must have...")
- [ ] Test with discretionary/preference clauses ("Preferably ISO 9001 certified...")
- [ ] Test with complex numeric thresholds (e.g. "Turnover > ₹5 Crore in last 3 FYs")

### 📋 Definition of Done
- [ ] Implementation complete
- [ ] Pytest passes (`pytest backend/tests/`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Documentation / docstrings updated
