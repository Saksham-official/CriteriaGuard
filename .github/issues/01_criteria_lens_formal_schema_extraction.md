# [CriteriaLens] Formal Schema Extraction: Automatically map financial, technical, and compliance mandates

## 🎯 Overview
In Indian public procurement (GeM, CPWD, Indian Railways, Defense/CRPF, State Tenders), tender documents easily exceed 50–150+ pages. The requirements are scattered across General Conditions of Contract (GCC), Special Conditions (SCC), technical specifications, and annexures.

Stage 1 of CriteriaGuard (**CriteriaLens**) is responsible for parsing unstructured tender documents and mapping them into a formal, structured schema. We need to upgrade CriteriaLens to reliably extract, normalize, and validate all tender mandates across three primary categories:

1. **Financial Mandates**: Turnover, Net Worth, Solvency, EMD, PBG, and Working Capital.
2. **Technical Qualifications**: Past experience, 80:50:40 rule for similar works, technical certifications (ISO, BIS), equipment/machinery capabilities.
3. **Statutory & Compliance Mandates**: GSTIN, PAN, PF/ESIC registration, MSME/NSIC exemptions, Make-in-India (MII) preference class (Class-I / Class-II local supplier), and non-blacklisting affidavits.

---

## 🔍 Current State
- `backend/engines/criteria_lens.py` sends chunked text (up to 12k chars) to Groq LLMs (Llama 3.3 70B / Llama 4 Scout / Qwen).
- It parses results into `CriterionSchema` defined in `backend/models/criterion.py`.
- Basic coercion exists in `_coerce_criterion()`, but complex tables, multi-year turnover conditions, and nested eligibility clauses can result in validation errors or missing threshold units.

---

## 🛠️ Required Tasks & Implementation Scope

### 1. Robust Multi-Page Chunking & Context Preservation
- Improve document chunking in `backend/engines/criteria_lens.py` to recognize clause boundaries (e.g., `Clause 4.1`, `Section III`, `Annexure A`) rather than purely arbitrary character limits.
- Preserve table context when requirements appear in BOQ or evaluation tables across page breaks.

### 2. Deep Schema Normalization (`backend/models/criterion.py`)
- Enhance `ThresholdSchema` to support:
  - Multi-year conditions (e.g. `period: "last_3_years"`, `period: "last_5_years"`, `comparison: "average"` vs `"each_year"`).
  - Currency and unit conversion (standardizing Crore, Lakh, INR, %, years, units).
  - Similar work ratios (e.g., 80:50:40 rule where bidder can submit 1 work @ 80%, 2 works @ 50%, or 3 works @ 40% value).

### 3. Pydantic v2 Parsing & Error Recovery
- Enhance `_coerce_criterion` to handle common LLM output anomalies (e.g. JSON strings with embedded quotes, null vs "null", mixed numeric types).
- Add clear logging when a criterion fails validation, ensuring partial failures do not discard valid extractions from the same chunk.

### 4. Comprehensive Unit & Integration Tests
- Create test cases in `backend/tests/test_criteria_lens.py` using synthetic tender text snippets reflecting GeM and CPWD tenders.
- Test edge cases: tenders with no financial criteria, tenders with only compliance criteria, and tenders with multiple currency notations (e.g., "₹ 5.00 Cr", "INR 50,000,000", "500 Lakhs").

---

## 📋 Acceptance Criteria
- [ ] Financial, technical, and compliance mandates are extracted with verbatim text citations and exact clause/page references.
- [ ] Numeric thresholds are properly normalized to floats with explicit units (`crore`, `lakh`, `years`, `percentage`).
- [ ] Pytest passes for all extraction scenarios with mocked LLM responses.
- [ ] No regression on existing tender ingestion endpoints in `backend/routers/tenders.py`.

---

## 💡 Contributor Guidance
- **Prerequisites**: Python 3.11, Pydantic v2, pytest.
- **Key Files**:
  - `backend/engines/criteria_lens.py`
  - `backend/models/criterion.py`
  - `backend/prompts/criteria_extraction.py`
  - `backend/tests/test_criteria_lens.py`
- **Branch Naming**: `feat/criterialens-formal-schema-extraction`
- Please refer to [CONTRIBUTING.md](../../CONTRIBUTING.md) for local environment setup instructions.
