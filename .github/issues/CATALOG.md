# 📋 CriteriaGuard Open Source Issue Catalog (15 Good First Issues)

This catalog breaks down large contributor tracks into **15 well-scoped, testable issues** categorized by label and difficulty. Maintainers can post these directly to GitHub Issues, and contributors can claim them immediately without needing Groq or Supabase API keys.

---

## 📊 Summary Table

| # | Issue Title | Labels | Difficulty | Primary Area |
| :-: | :--- | :--- | :---: | :--- |
| **01** | Add sample tender JSON fixture for CriteriaLens | `good first issue`, `backend`, `testing` | **Easy** | Backend / Testing |
| **02** | Add Pydantic validation for missing/invalid criteria fields | `good first issue`, `backend` | **Easy** | Backend / Schema |
| **03** | Write tests for mandatory vs optional clause classification | `good first issue`, `nlp`, `testing` | **Medium** | NLP / Deontic Logic |
| **04** | Add UI state for approved, rejected, and needs-review criteria | `good first issue`, `frontend` | **Easy** | Frontend / UI |
| **05** | Improve accessibility (a11y) of officer approval dashboard | `a11y`, `frontend` | **Medium** | Frontend / Accessibility |
| **06** | Add empty and error states to verdict dashboard | `frontend`, `ux` | **Easy** | Frontend / UX |
| **07** | Add API error responses with consistent HTTP status codes | `backend`, `api` | **Medium** | Backend / API |
| **08** | Add unit tests for SHA-256 audit-chain append logic | `backend`, `security`, `testing` | **Medium** | Security / Audit |
| **09** | Add CSV export for evaluation results | `feature`, `backend` | **Medium** | Backend / Reporting |
| **10** | Add comprehensive documentation for criteria schema | `documentation`, `good first issue` | **Easy** | Documentation |
| **11** | Add screenshot/GIF visual walkthrough to README | `documentation`, `good first issue` | **Easy** | Visual / Showcase |
| **12** | Add GitHub issue and pull-request YAML templates | `documentation`, `ci` | **Easy** | Community / Governance |
| **13** | Add SECURITY.md with responsible disclosure instructions | `security`, `documentation` | **Easy** | Security / Governance |
| **14** | Add Docker Compose for frontend, backend, and Postgres | `devops`, `infrastructure` | **Medium** | DevOps / Tooling |
| **15** | Add CI workflow for lint, type-check, and automated tests | `ci`, `good first issue` | **Easy** | CI / Automation |

---

## Detailed Specifications

### Issue 01: Add sample tender JSON fixture for CriteriaLens
- **Difficulty**: Easy
- **Labels**: `good first issue`, `backend`, `testing`
- **Objective**: Provide structured procurement JSON fixtures in `backend/tests/fixtures/sample_tender.json` containing financial (turnover, net worth), technical (project experience, personnel), and compliance clauses.
- **Acceptance Criteria**:
  - Fixture valid against `CriterionSchema`.
  - Loaded cleanly in unit tests without file path errors.
  - Test command: `pytest backend/tests/test_rules_engine.py`

### Issue 02: Add Pydantic validation for missing/invalid criteria fields
- **Difficulty**: Easy
- **Labels**: `good first issue`, `backend`
- **Objective**: Ensure `CriterionSchema` in `backend/models/criterion.py` gracefully handles edge-case values from LLM extraction, rejecting malformed thresholds and invalid deontic confidences.
- **Acceptance Criteria**:
  - Unit tests covering negative thresholds, null categories, and empty strings.
  - Helpful validation error messages logged.

### Issue 03: Write tests for mandatory vs optional clause classification
- **Difficulty**: Medium
- **Labels**: `good first issue`, `nlp`, `testing`
- **Objective**: Expand test cases for linguistic markers distinguishing binding obligations ("shall", "must", "strictly required") from advisory preferences ("should", "desirable", "preferred").
- **Acceptance Criteria**:
  - Minimum 10 deontic modal test assertions.
  - Verifies ambiguous clauses default to human officer review.

### Issue 04: Add UI state for approved, rejected, and needs-review criteria
- **Difficulty**: Easy
- **Labels**: `good first issue`, `frontend`
- **Objective**: In `frontend/src/pages/CriteriaReview.jsx`, render distinct visual badges with clear colors and icons for `Approved` (green), `Rejected` (red), and `Needs Review` (amber).
- **Acceptance Criteria**:
  - High-contrast visual indicators.
  - Status updates update in real-time when clicking approve/reject.

### Issue 05: Improve accessibility (a11y) of officer approval dashboard
- **Difficulty**: Medium
- **Labels**: `a11y`, `frontend`
- **Objective**: Add keyboard navigation (`Tab`, `Enter`, `Esc`), ARIA labels, and WCAG AA contrast compliance to `CriteriaReview.jsx` and `ReviewQueue.jsx`.
- **Acceptance Criteria**:
  - All interactive buttons and modals accessible via keyboard.
  - Screen reader friendly table headings.

### Issue 06: Add empty and error states to verdict dashboard
- **Difficulty**: Easy
- **Labels**: `frontend`, `ux`
- **Objective**: Enhance `frontend/src/pages/Dashboard.jsx` and `ComparativeMatrix.jsx` with helpful illustrations and actions when zero bidders are uploaded or network requests fail.
- **Acceptance Criteria**:
  - "No bidders uploaded yet" CTA button redirecting to upload.
  - Retry button on failed API requests.

### Issue 07: Add API error responses with consistent HTTP status codes
- **Difficulty**: Medium
- **Labels**: `backend`, `api`
- **Objective**: Standardize API exception responses across `backend/routers/` to return uniform `{ "detail": "...", "error_code": "..." }` schemas and proper HTTP 400/404/422 status codes.
- **Acceptance Criteria**:
  - Invalid UUIDs or non-existent tender IDs return 404 rather than 500.
  - Error schemas documented in FastAPI `/docs`.

### Issue 08: Add unit tests for SHA-256 audit-chain append logic
- **Difficulty**: Medium
- **Labels**: `backend`, `security`, `testing`
- **Objective**: Add tests in `backend/tests/test_audit_chain.py` verifying hash calculations, previous-hash linkage, and tamper detection when historic log entries are altered.
- **Acceptance Criteria**:
  - Genesis block verification.
  - Re-evaluating tampered entries invalidates subsequent hash links.

### Issue 09: Add CSV export for evaluation results
- **Difficulty**: Medium
- **Labels**: `feature`, `backend`
- **Objective**: Add a `GET /api/reports/export-csv/{tender_id}` endpoint exporting bidder comparative evaluation matrix as downloadable CSV.
- **Acceptance Criteria**:
  - Columns: Bidder Name, Criterion Code, Status, Extracted Value, Threshold, Citation Page.
  - Proper MIME type `text/csv` and Content-Disposition headers.

### Issue 10: Add comprehensive documentation for criteria schema
- **Difficulty**: Easy
- **Labels**: `documentation`, `good first issue`
- **Objective**: Document `CriterionSchema` and `ExtractionSchema` in `docs/SCHEMA.md` with example JSON payloads, data types, and enum descriptions.
- **Acceptance Criteria**:
  - Markdown table of all fields, types, and descriptions.
  - Copyable JSON example snippets.

### Issue 11: Add screenshot/GIF visual walkthrough to README
- **Difficulty**: Easy
- **Labels**: `documentation`, `good first issue`
- **Objective**: Capture and embed clean screenshots/GIFs of the officer approval dashboard, comparative matrix, and audit trail in `README.md`.
- **Acceptance Criteria**:
  - Compressed WebP/PNG assets stored under `docs/assets/`.
  - Alt tags included for accessibility.

### Issue 12: Add GitHub issue and pull-request YAML templates
- **Difficulty**: Easy
- **Labels**: `documentation`, `ci`
- **Objective**: Provide structured GitHub Issue Forms (`bug_report.yml`, `feature_request.yml`) and a comprehensive PR template with governance checklists.
- **Acceptance Criteria**:
  - Located in `.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE.md`.
  - Validated by GitHub repository health.

### Issue 13: Add SECURITY.md with responsible disclosure instructions
- **Difficulty**: Easy
- **Labels**: `security`, `documentation`
- **Objective**: Add root `SECURITY.md` defining scope for government tender integrity, deterministic rules, and private disclosure channels.
- **Acceptance Criteria**:
  - GitHub Security tab recognizes active security policy.
  - Private reporting email and vulnerability timeline defined.

### Issue 14: Add Docker Compose for frontend, backend, and Postgres
- **Difficulty**: Medium
- **Labels**: `devops`, `infrastructure`
- **Objective**: Provide `docker-compose.yml` orchestrating FastAPI backend, React frontend, and PostgreSQL with offline mock mode enabled by default.
- **Acceptance Criteria**:
  - `docker compose up` brings up all services without error.
  - Volume persistence for database data.

### Issue 15: Add CI workflow for lint, type-check, and automated tests
- **Difficulty**: Easy
- **Labels**: `ci`, `good first issue`
- **Objective**: Ensure `.github/workflows/ci.yml` runs Ruff linting, Black formatting, pytest suite, and frontend build on every pull request.
- **Acceptance Criteria**:
  - Runs in under 3 minutes.
  - Tests execute in `MOCK_LLM=true` mode without external API secrets.
