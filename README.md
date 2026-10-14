# 🛡️ CriteriaGuard: Governance-Grade AI for Procurement
**Explainable AI & Deterministic Verification Platform for Government Tender Eligibility**

[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen?style=for-the-badge&logo=githubactions)](.github/workflows/ci.yml)
[![Mock Mode](https://img.shields.io/badge/Mock%20Mode-Zero%20API%20Keys%20Required-blueviolet?style=for-the-badge)](#-run-without-api-keys-mock-mode)
[![Good First Issues](https://img.shields.io/badge/Good%20First%20Issues-15%20Available-orange?style=for-the-badge)](https://github.com/Saksham-official/CriteriaGuard/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-emerald?style=for-the-badge)](CONTRIBUTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy%20Active-critical?style=for-the-badge)](SECURITY.md)

CriteriaGuard is an open-source, high-integrity platform engineered to automate the tedious, high-stakes process of cross-checking bidder proposals against tender eligibility criteria. Built for **public procurement transparency and civic accountability**, it guarantees that every evaluation verdict is **100% deterministic, source-cited, and cryptographically auditable**.

---

## 📸 Interface Preview & Workflow

```
[ Tender Document (100+ pages) ] 
               │
               ▼
   ╔═════════════════════════════════════════════════════════════════════╗
   ║  STAGE 1: CriteriaLens (Tender Intelligence)                       ║
   ║  - Extracts clauses into structured schema                          ║
   ║  - Analyzes linguistic deontic markers ("shall" vs "should")        ║
   ╚═════════════════════════════════════════════════════════════════════╝
               │
               ▼
   ╔═════════════════════════════════════════════════════════════════════╗
   ║  OFFICER CHECKPOINT (Human-in-the-Loop)                             ║
   ║  Procurement Officer reviews, adjusts, & signs off criteria         ║
   ╚═════════════════════════════════════════════════════════════════════╝
               │
               ▼
   ╔═════════════════════════════════════════════════════════════════════╗
   ║  STAGE 2: DocProbe (Bidder Understanding & Citations)               ║
   ║  - Scans proposals, audited balance sheets, & certificates          ║
   ║  - Anchors exact citations (Doc name, page number, excerpt)         ║
   ╚═════════════════════════════════════════════════════════════════════╝
               │
               ▼
   ╔═════════════════════════════════════════════════════════════════════╗
   ║  STAGE 3: VerdictCore & RulesEngine (Deterministic Logic)           ║
   ║  - Zero LLM hallucinations in decisions (Pure Python rules)         ║
   ║  - Auto-flags borderline values (within 10%) for officer review     ║
   ║  - Appends tamper-evident SHA-256 chained audit logs                ║
   ╚═════════════════════════════════════════════════════════════════════╝
               │
               ▼
[ Interactive Comparative Matrix ] ───► [ Signed PDF Governance Report ]
```

---

## 🏛️ Why This Matters: The "Governance Gap"

In public procurement (ministries, state departments, defense organizations, municipal corporations), evaluation committees manually review hundreds of pages across dozens of competing bidders:

- **The Legal Risk**: A single overlooked mandatory requirement leads to wrongful disqualification, bidder litigation, or court injunctions halting vital infrastructure projects.
- **The Transparency Gap**: Manual decisions are often undocumented and vulnerable to Right to Information (RTI) inquiries or accusations of favoritism.
- **The AI Trap**: Generic "black-box" LLM wrappers frequently hallucinate financial figures or fail on nuanced legal language—an unacceptable failure mode in public administration.

**CriteriaGuard solves this** by cleanly separating **AI for text extraction** from **pure deterministic code for evaluation**. AI finds the facts; verifiable Python rules make the decision.

---

## 📖 Glossary

Domain-specific procurement vocabulary can be intimidating. Here is a quick reference:

| Term | Definition |
| :--- | :--- |
| **Tender (RFP)** | A formal government solicitation inviting suppliers to submit proposals for goods, works, or services. |
| **Bidder** | An enterprise or joint venture submitting a formal proposal to win the contract. |
| **Eligibility Criterion** | A mandatory or technical condition that a bidder must satisfy to avoid disqualification. |
| **CriteriaLens** | Stage 1 engine: Extracts and structures eligibility clauses from tender documents into Pydantic models. |
| **DocProbe** | Stage 2 engine: Locates supporting evidence and verbatim citations across bidder submissions. |
| **VerdictCore** | Stage 3 engine: Evaluates extracted evidence against criteria using deterministic Python rules. Zero LLMs involved in final decisions. |
| **Deontic Modality** | Legal distinction between binding obligations (*"shall"*, *"must"*) and advisory preferences (*"should"*, *"preferred"*). |
| **Borderline Value** | Numeric evidence that falls within 10% of a threshold (e.g. ₹4.95 Cr vs ₹5 Cr requirement), automatically flagged for human officer sign-off. |

---

## 🚀 Run Without API Keys (Mock Mode)

CriteriaGuard includes an **offline contributor mock mode**. You can explore the full UI, REST API, modular rules engine, and cryptographic audit workflow without creating a Groq account or setting up Supabase:

```bash
# 1. Clone repository
git clone https://github.com/Saksham-official/CriteriaGuard.git
cd CriteriaGuard

# 2. Configure mock mode (No API keys needed!)
cp .env.example .env
export MOCK_LLM=true
export USE_SAMPLE_DATA=true

# 3. Launch Backend
cd backend
pip install -r requirements.txt
pytest
python main.py
```

In a second terminal window, launch the frontend:

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to explore the complete platform with pre-seeded tender and bidder data!

---

## 📂 Project Structure

```text
CriteriaGuard/
├── .github/
│   ├── ISSUE_TEMPLATE/        # Structured GitHub Issue Forms (bug, feature)
│   ├── issues/                # 15 beginner-friendly good first issues
│   ├── workflows/             # GitHub Actions CI automated pipeline
│   └── PULL_REQUEST_TEMPLATE  # Governance and quality checklist
├── backend/
│   ├── engines/               # Core pipeline engines (CriteriaLens, DocProbe, VerdictCore)
│   ├── rules/                 # Modular, extensible deterministic rules engine
│   │   ├── base.py            # EligibilityRule base class & RuleResult schema
│   │   ├── numeric_threshold.py    # Greater/less than, count & borderline checks
│   │   ├── mandatory_document.py   # Required certificates & compliance checklist
│   │   └── experience_requirement.py # Technical track record & years experience
│   ├── routers/               # FastAPI endpoints (tenders, bidders, verdicts, audit)
│   ├── services/              # SHA-256 audit log, PDF/DOCX parsing, OCR
│   ├── models/                # Pydantic schemas (CriterionSchema, ExtractionSchema)
│   ├── db/                    # Supabase client + In-memory Mock DB
│   └── tests/
│       ├── fixtures/          # Sample tender & bidder JSON fixtures
│       ├── test_numeric_threshold.py
│       ├── test_rules_engine.py
│       ├── test_audit_chain.py
│       └── test_mock_pipeline.py
├── frontend/                  # React 18 (Vite) Glassmorphism dashboard
│   └── src/pages/             # Upload, CriteriaReview, ComparativeMatrix, AuditTrail
├── docker-compose.yml         # Containerized local environment
├── CONTRIBUTING.md            # Comprehensive contributor guidelines
├── SECURITY.md                # Vulnerability disclosure & scope
└── README.md
```

---

## 🧩 Adding a Custom Eligibility Rule (In 5 Minutes)

You don't need to know LLMs or OCR to contribute! CriteriaGuard exposes an easy extension point:

```python
from rules import EligibilityRule, RuleResult, default_engine

class ConsortiumMemberRule(EligibilityRule):
    rule_id = "consortium_member_limit"
    name = "Consortium Member Limit Rule"
    description = "Joint ventures must have at most 3 consortium partners."

    def applies_to(self, criterion: dict, evidence: dict) -> bool:
        return "consortium" in str(criterion.get("text", "")).lower()

    def evaluate(self, criterion: dict, evidence: dict) -> RuleResult:
        count = evidence.get("extracted_value_numeric", 0)
        if count > 3:
            return RuleResult(
                status="Not Eligible",
                reason=f"Consortium has {count} members, exceeding maximum allowed limit of 3."
            )
        return RuleResult(
            status="Eligible",
            reason=f"Consortium has {count} members (within limit <= 3)."
        )

# Register into the live evaluation pipeline
default_engine.register_rule(ConsortiumMemberRule())
```

Add your rule in `backend/rules/`, write a unit test in `backend/tests/`, and submit a PR!

---

## 🌱 Good First Issues (Claim Yours!)

We have converted large tracks into **15 self-contained, testable issues**:

| # | Issue Title | Labels | Difficulty | Ready to Claim |
| :-: | :--- | :--- | :---: | :---: |
| **01** | Add sample tender JSON fixture for CriteriaLens | `good first issue`, `backend`, `testing` | **Easy** | [Claim #5](https://github.com/Saksham-official/CriteriaGuard/issues/5) |
| **02** | Add Pydantic validation for missing/invalid criteria fields | `good first issue`, `backend` | **Easy** | [Claim #6](https://github.com/Saksham-official/CriteriaGuard/issues/6) |
| **03** | Write tests for mandatory vs optional clause classification | `good first issue`, `nlp`, `testing` | **Medium** | [Claim #7](https://github.com/Saksham-official/CriteriaGuard/issues/7) |
| **04** | Add UI state for approved, rejected, and needs-review criteria | `good first issue`, `frontend` | **Easy** | [Claim #8](https://github.com/Saksham-official/CriteriaGuard/issues/8) |
| **05** | Improve accessibility (a11y) of officer approval dashboard | `a11y`, `frontend` | **Medium** | [Claim #9](https://github.com/Saksham-official/CriteriaGuard/issues/9) |
| **06** | Add empty and error states to verdict dashboard | `frontend`, `ux` | **Easy** | [Claim #10](https://github.com/Saksham-official/CriteriaGuard/issues/10) |
| **07** | Add API error responses with consistent HTTP status codes | `backend`, `api` | **Medium** | [Claim #11](https://github.com/Saksham-official/CriteriaGuard/issues/11) |
| **08** | Add unit tests for SHA-256 audit-chain append logic | `backend`, `security`, `testing` | **Medium** | [Claim #12](https://github.com/Saksham-official/CriteriaGuard/issues/12) |
| **09** | Add CSV export for evaluation results | `feature`, `backend` | **Medium** | [Claim #13](https://github.com/Saksham-official/CriteriaGuard/issues/13) |
| **10** | Add comprehensive documentation for criteria schema | `documentation`, `good first issue` | **Easy** | [Claim #14](https://github.com/Saksham-official/CriteriaGuard/issues/14) |
| **11** | Add screenshot/GIF visual walkthrough to README | `documentation`, `good first issue` | **Easy** | [Claim #15](https://github.com/Saksham-official/CriteriaGuard/issues/15) |
| **12** | Add GitHub issue and pull-request YAML templates | `documentation`, `ci` | **Easy** | [Claim #16](https://github.com/Saksham-official/CriteriaGuard/issues/16) |
| **13** | Add SECURITY.md with responsible disclosure instructions | `security`, `documentation` | **Easy** | [Claim #17](https://github.com/Saksham-official/CriteriaGuard/issues/17) |
| **14** | Add Docker Compose for frontend, backend, and Postgres | `devops`, `infrastructure` | **Medium** | [Claim #18](https://github.com/Saksham-official/CriteriaGuard/issues/18) |
| **15** | Add CI workflow for lint, type-check, and automated tests | `ci`, `good first issue` | **Easy** | [Claim #19](https://github.com/Saksham-official/CriteriaGuard/issues/19) |

👉 Browse and claim all active issues directly in the [GitHub Issues Tab](https://github.com/Saksham-official/CriteriaGuard/issues). Reference specifications are also maintained in [.github/issues/CATALOG.md](.github/issues/CATALOG.md).

---

## 🧪 Testing & Quality Assurance

Run the test suite locally with pytest:

```bash
cd backend
pytest -v
```

Run code formatting and static type checking:

```bash
# Linting & Formatting
ruff check .
black --check .

# Static type analysis
mypy .
```

All pull requests run automated checks via [GitHub Actions CI](.github/workflows/ci.yml).

---

## 🐳 Docker Quickstart

To run the entire stack with Docker Compose:

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

---

## 🗺️ Roadmap & Future Capabilities

- [x] Contributor Mock Mode & Offline Seeded Pipeline
- [x] Modular Extensible Rules Engine (`backend/rules/`)
- [x] SHA-256 Chained Audit Trail & Verification Endpoint
- [ ] Multi-lingual OCR & Indic Language Translation (Hindi, Tamil, Marathi)
- [ ] Exportable CSV / Excel Comparative Evaluation Matrix
- [ ] Automated GeM (Government e-Marketplace) API integration
- [ ] WCAG AA Full Accessibility Compliance & Dark/Light Theme Switching

---

## 🤝 Community & Recognition

We love our contributors! Every approved PR gets:
1. Listed in the contributor hall of fame.
2. A shoutout in our community updates and release notes.
3. Review feedback within 24 hours.

Please review our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting a pull request.

---

*“Built for the realities of Public Procurement—where accountability meets intelligence.”* 🛡️
