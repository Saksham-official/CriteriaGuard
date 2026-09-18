## 📌 Pull Request Description

### 🔗 Related Issue
Closes #[issue number]

---

### 📝 Summary of Changes
- 
- 
- 

---

### 🏛️ Core Governance Invariants Checklist
CriteriaGuard is engineered for Indian Government Procurement governance. Please confirm:
- [ ] **Deterministic Verdicts**: No LLM calls were added to `verdict_core.py` or final eligibility decision logic.
- [ ] **Explainability (XAI)**: All extracted criteria and bidder findings include source citations (page, clause, excerpt).
- [ ] **Audit Integrity**: State transitions, overrides, or status updates are properly recorded in the audit log.

---

### 🧪 Testing & Quality Checks
- [ ] Backend tests added/updated and passing (`pytest backend/tests/`)
- [ ] Code formatted with Black & Ruff (`pre-commit run --all-files` or `ruff check .`)
- [ ] Type hints validated with MyPy (`mypy backend/`)
- [ ] Frontend builds cleanly without console errors (`npm run build` inside `frontend/`)
- [ ] Tested manually against sample tender/bidder documents

---

### 📸 Screenshots / Demos (If Applicable)
_Add screenshots or a quick recording if your changes affect the UI._

---

### 🤝 Contributor Agreement
- [ ] I have read and agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- [ ] I have read and followed the [Contributing Guidelines](CONTRIBUTING.md).
