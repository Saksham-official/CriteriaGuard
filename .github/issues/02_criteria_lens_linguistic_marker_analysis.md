# [CriteriaLens] Linguistic Marker Analysis: Classify mandatory obligations vs optional preferences

## 🎯 Overview
In government tender adjudication, a single word can make the difference between outright bidder disqualification and a non-critical preference.

Legal tender documents use **deontic modality** keywords to express obligations:
- **Mandatory Requirements (Disqualifying)**: Words like `"shall"`, `"must"`, `"mandatorily"`, `"is required to"`, `"essential"`, `"non-negotiable"`, or `"failure to submit shall result in rejection"`.
- **Optional Preferences (Non-disqualifying)**: Words like `"should"`, `"preferred"`, `"desirable"`, `"may"`, `"encouraged"`, or `"advisable"`.
- **Ambiguous / Conditional Clauses**: Mixed phrases like `"shall preferably"`, `"should normally"`, or `"may at the discretion of the committee"`.

Relying solely on LLM interpretation can lead to hallucinations where an optional preference is classified as a mandatory disqualification criterion, or vice-versa. To uphold our core principle of **explainable, deterministic governance**, we need a dedicated **Linguistic Marker Analysis** engine.

---

## 🔍 Current State
- `backend/prompts/criteria_extraction.py` advises the LLM to look for `"shall"`, `"must"`, and `"essential"`.
- However, there is **no deterministic verification** of the text against linguistic keyword dictionaries.
- If the LLM marks `mandatory: true` on a clause containing `"The bidder should preferably have CMMI Level 3"`, the system currently has no rule-based cross-check to flag this discrepancy.

---

## 🛠️ Required Tasks & Implementation Scope

### 1. Build `backend/engines/linguistic_analyzer.py`
Create a modular linguistic analyzer that executes deterministic pattern matching on verbatim criteria text:
- **Mandatory Marker Set**: `["shall", "must", "mandatorily", "is required to", "essential", "strictly", "compulsory", "sole criteria", "condition precedent"]`
- **Discretionary / Preference Set**: `["should", "preferred", "desirable", "may", "encouraged", "optional", "advisable"]`
- **Rejection Triggers**: Regex patterns matching `"will lead to rejection"`, `"summarily rejected"`, `"disqualified"`.

### 2. Modality Conflict Detection & Confidence Scoring
- Compare the LLM's classification against the deterministic linguistic marker result:
  - If linguistic markers agree with the LLM -> `mandatory_confidence = "high"`.
  - If linguistic markers conflict (e.g. LLM says `mandatory=true`, but text has `"should"` or `"desirable"`) -> automatically set `mandatory_confidence = "ambiguous"` and flag for officer review.
  - If text contains conflicting words (e.g. `"shall preferably"`) -> flag as `"ambiguous"` with rationale.

### 3. Update `CriterionSchema`
Update `backend/models/criterion.py` to store linguistic metadata:
```python
class LinguisticMarkerSchema(BaseModel):
    detected_marker: Optional[str] = None       # e.g., "shall", "must", "should", "preferred"
    marker_category: Optional[str] = None     # "mandatory" | "discretionary" | "ambiguous"
    rationale: Optional[str] = None           # "Identified strict obligation keyword 'shall'"
```

### 4. Comprehensive Unit Test Suite
Add test cases in `backend/tests/test_linguistic_analyzer.py`:
- Test clauses with unambiguous mandatory keywords (`"shall submit EMD"`).
- Test clauses with preference keywords (`"bidder should preferably possess ISO 27001"`).
- Test clauses with negation and rejection phrases (`"failure to submit will result in disqualification"`).
- Test ambiguous compound clauses.

---

## 📋 Acceptance Criteria
- [ ] Deterministic linguistic analysis runs on all extracted criteria without requiring external network calls.
- [ ] Conflicting or ambiguous modality triggers `mandatory_confidence = "ambiguous"`.
- [ ] Detected marker and category are exposed in the criterion payload for frontend presentation.
- [ ] 100% test coverage on linguistic keyword patterns.

---

## 💡 Contributor Guidance
- **Prerequisites**: Python 3.11, regular expressions (regex), Pydantic v2.
- **Key Files**:
  - `backend/engines/linguistic_analyzer.py` (New)
  - `backend/engines/criteria_lens.py`
  - `backend/models/criterion.py`
  - `backend/tests/test_linguistic_analyzer.py` (New)
- **Branch Naming**: `feat/criterialens-linguistic-marker-analysis`
- Please refer to [CONTRIBUTING.md](../../CONTRIBUTING.md) for local environment setup instructions.
