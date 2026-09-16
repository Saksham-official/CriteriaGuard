# 🤝 Contributing to CriteriaGuard

Thank you for your interest in contributing to **CriteriaGuard**! 

CriteriaGuard is a governance-grade, explainable AI platform designed to evaluate Indian government tender eligibility deterministically and transparently. Because this system is engineered for high-stakes public procurement (where transparency, determinism, and anti-corruption audit trails are paramount), we hold our codebase to rigorous engineering, testing, and security standards.

This document provides a comprehensive guide for contributors, covering everything from initial local setup to coding standards, branching strategies, automated testing, and pre-commit checks.

---

## 📑 Table of Contents

1. [Governance & Core Engineering Principles](#-governance--core-engineering-principles)
2. [Prerequisites](#-prerequisites)
3. [Local Development Setup](#-local-development-setup)
   - [1. Fork and Clone Repository](#1-fork-and-clone-repository)
   - [2. Backend Setup (FastAPI & Python)](#2-backend-setup-fastapi--python)
   - [3. Frontend Setup (React & Vite)](#3-frontend-setup-react--vite)
4. [Running Tests & Quality Checks](#-running-tests--quality-checks)
   - [Backend Tests (pytest)](#backend-tests-pytest)
   - [Frontend Quality Checks](#frontend-quality-checks)
5. [Pre-commit & Code Quality Tooling](#-pre-commit--code-quality-tooling)
   - [Pre-commit Hooks Setup](#pre-commit-hooks-setup)
   - [Ruff (Linting & Formatting)](#ruff-linting--formatting)
   - [Black (Deterministic Code Formatting)](#black-deterministic-code-formatting)
   - [MyPy (Static Type Checking)](#mypy-static-type-checking)
6. [Branching Conventions & Git Workflow](#-branching-conventions--git-workflow)
   - [Branch Naming Conventions](#branch-naming-conventions)
   - [Commit Message Guidelines](#commit-message-guidelines)
   - [Pull Request (PR) Workflow](#pull-request-pr-workflow)
7. [Coding Standards](#-coding-standards)
   - [Python & FastAPI Standards](#python--fastapi-standards)
   - [React & Frontend Standards](#react--frontend-standards)
   - [Security & Anti-Tampering Standards](#security--anti-tampering-standards)
8. [Reporting Issues & Getting Help](#-reporting-issues--getting-help)

---

## 🏛️ Governance & Core Engineering Principles

Before writing code, please keep our three core system pillars in mind:

1. **Deterministic Verdicts (Zero LLM Hallucinations in Decisions)**:
   - LLMs (Llama 3.3 via Groq) are used **strictly for unstructured text extraction** and document structuring (`CriteriaLens` and `DocProbe`).
   - Final eligibility verdicts (`Eligible`, `Not Eligible`, `Needs Review`) **must be calculated through pure deterministic Python logic** in `backend/engines/verdict_core.py`.
   - Never introduce LLM calls to directly decide a bidder's legal or technical qualification.
2. **Explainability & Source Citations (XAI)**:
   - Every extraction and verdict must be traceable to a specific source document, page number, and text excerpt.
3. **Audit Integrity**:
   - All state transitions and officer interventions must be recorded in tamper-evident logs chained via SHA-256 hashes.

---

## 🛠️ Prerequisites

Ensure you have the following installed on your workstation:

| Tool | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11+` | `3.11.9` | Required for backend, typing features, and dependencies |
| **Node.js** | `18.0+` | `20.x` or `22.x LTS` | Required for building and running the Vite frontend |
| **npm** | `9.0+` | `10.x+` | Package manager for frontend dependencies |
| **Git** | `2.30+` | Latest | Distributed version control |
| **Tesseract OCR** | `5.0+` | Optional | Optional local fallback for scanned document OCR |

---

## 🚀 Local Development Setup

### 1. Fork and Clone Repository

1. Fork the repository on GitHub: [https://github.com/Saksham-official/CriteriaGuard](https://github.com/Saksham-official/CriteriaGuard).
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/CriteriaGuard.git
   cd CriteriaGuard
   ```
3. Set the upstream remote to sync future updates:
   ```bash
   git remote add upstream https://github.com/Saksham-official/CriteriaGuard.git
   ```

---

### 2. Backend Setup (FastAPI & Python)

The backend is built with FastAPI, PyMuPDF, pdfplumber, and Pydantic v2.

#### Step 2.1: Navigate to Backend Directory
```bash
cd backend
```

#### Step 2.2: Create and Activate a Virtual Environment

- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(If you encounter execution policy restrictions, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **Windows (Command Prompt)**:
  ```cmd
  python -m venv venv
  .\venv\Scripts\activate.bat
  ```

#### Step 2.3: Install Dependencies

Install runtime dependencies and developer tooling:

```bash
# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install core runtime requirements
pip install -r requirements.txt

# Install development and testing dependencies (pytest, ruff, black, mypy, pre-commit)
pip install -r requirements-dev.txt
```

> [!TIP]
> If `requirements-dev.txt` is not yet installed or you want to install dev tools directly:
> ```bash
> pip install pytest pytest-asyncio httpx ruff black mypy pre-commit
> ```

#### Step 2.4: Configure Environment Variables

Create your local `.env` configuration from `.env.example`:

- **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```
- **Windows (PowerShell)**:
  ```powershell
  Copy-Item .env.example .env
  ```

Open `.env` in your editor and configure the necessary credentials:

```dotenv
# Groq Cloud API Key for Llama 3 extraction models (Required for AI extraction)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Supabase PostgreSQL Database credentials (Required for storage and audit trails)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key-here
SUPABASE_KEY=your-supabase-anon-key-here

# Google Cloud Vision API Key (Optional: for cloud OCR fallback)
GOOGLE_CLOUD_VISION_API_KEY=AIzaSy...

# Application Security
SECRET_KEY=dev-secret-key-change-in-production-criteria-guard
ENVIRONMENT=development
```

#### Step 2.5: Run the Backend Server

Start the FastAPI development server with auto-reload enabled:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
or:
```bash
python main.py
```

Verify that the backend is running:
- **API Root / Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 3. Frontend Setup (React & Vite)

The frontend is a modern React application built using Vite, Tailwind CSS, and WebGL (Aurora) visual layers.

#### Step 3.1: Navigate to Frontend Directory
From the project root:
```bash
cd frontend
```

#### Step 3.2: Install Node Dependencies
```bash
npm install
```

#### Step 3.3: Start Frontend Development Server
```bash
npm run dev
```

The frontend should now be running at:
- **Local Application URL**: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Running Tests & Quality Checks

### Backend Tests (pytest)

All unit and integration tests are organized under `backend/tests/`. We test:
1. **Deterministic Logic (`VerdictCore`)**: Verifying threshold comparisons, borderline flags (10% proximity), mandatory vs. optional requirements, and ambiguous criteria handling.
2. **Document Tampering & Security (`SecurityShield`)**: Validating PDF/Image EXIF metadata scans, hidden text layer detection, and prompt injection defense.
3. **API Endpoints**: Validating FastAPI request/response contracts and error handling.

#### Run the Test Suite:

From the `backend` directory (with your virtual environment active):

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with code coverage report
pytest --cov=engines --cov=services --cov=routers

# Run a specific test file
pytest tests/test_verdict_core.py
```

### Frontend Quality Checks

From the `frontend` directory:

```bash
# Run ESLint to detect syntax or styling problems
npm run lint

# Verify production build compilation
npm run build
```

---

## 🧰 Pre-commit & Code Quality Tooling

To ensure consistent formatting, prevent broken commits, and maintain high static-analysis standards, CriteriaGuard uses **pre-commit** hooks along with **Ruff**, **Black**, and **MyPy**.

### Pre-commit Hooks Setup

Install and activate the pre-commit git hooks in your cloned repository:

```bash
# Ensure pre-commit is installed (installed via requirements-dev.txt)
pre-commit --version

# Install the git hook scripts into .git/hooks/
pre-commit install
```

Once installed, pre-commit runs automatically whenever you execute `git commit`.

To manually run all hooks across all files in the repository:
```bash
pre-commit run --all-files
```

---

### Ruff (Linting & Formatting)

[Ruff](https://docs.astral.sh/ruff/) is an extremely fast Python linter and formatter that replaces Flake8, isort, and pyupgrade.

- **Check code for lint errors**:
  ```bash
  ruff check .
  ```
- **Automatically apply safe fixes**:
  ```bash
  ruff check --fix .
  ```
- **Check format without modifying**:
  ```bash
  ruff format --check .
  ```
- **Format code with Ruff**:
  ```bash
  ruff format .
  ```

---

### Black (Deterministic Code Formatting)

[Black](https://black.readthedocs.io/) is the uncompromising Python code formatter. We configure Black with a **100-character line length** to accommodate descriptive government procurement data structures and legal clause representations.

- **Check formatting compliance**:
  ```bash
  black --check backend/
  ```
- **Format files**:
  ```bash
  black backend/
  ```

---

### MyPy (Static Type Checking)

[MyPy](https://mypy.readthedocs.io/) enforces strict static type safety across our backend models, services, and engines.

- **Run type checks on the backend codebase**:
  ```bash
  mypy backend
  ```

---

## 🌿 Branching Conventions & Git Workflow

We use a feature-branch workflow. **Direct commits to `main` are strictly prohibited.**

### Branch Naming Conventions

Prefix your branch names with one of the following descriptors followed by a short, kebab-case description:

| Branch Prefix | Purpose | Example |
| :--- | :--- | :--- |
| `feat/` | A new feature, engine capability, or endpoint | `feat/bhashini-hindi-translation` |
| `fix/` | A bug fix in existing code | `fix/threshold-borderline-rounding` |
| `docs/` | Documentation changes or additions | `docs/contributing-guide` |
| `test/` | Adding, updating, or fixing tests | `test/verdict-core-thresholds` |
| `refactor/` | Code restructuring without feature changes | `refactor/pdf-extractor-modularization` |
| `security/` | Adversarial defense or security patches | `security/exif-metadata-sanitization` |
| `chore/` | Tooling, dependencies, or CI/CD updates | `chore/update-pre-commit-hooks` |

### Commit Message Guidelines

We follow the **Conventional Commits** specification:

```
<type>(<optional scope>): <imperative summary>

[optional body explaining motivation and architectural context]

[optional footer(s) referencing issue numbers]
```

**Common types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `security`.

**Examples**:
- `feat(verdict_core): add 10% borderline proximity review sub-reason`
- `fix(security_shield): prevent false positive on camera vendor exif tags`
- `docs(contributing): add local setup and pre-commit workflow guide`
- `test(engines): add unit tests for ambiguous mandatory criterion fallback`

---

### Pull Request (PR) Workflow

1. **Keep Your Fork Updated**:
   ```bash
   git checkout main
   git pull upstream main
   ```
2. **Create Your Working Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make Atomic Commits**:
   - Write clear, focused commits.
   - Run tests and pre-commit checks before pushing:
     ```bash
     pre-commit run --all-files
     pytest backend/tests
     ```
4. **Push to Your Fork**:
   ```bash
   git push -u origin feat/your-feature-name
   ```
5. **Open a Pull Request**:
   - Go to [https://github.com/Saksham-official/CriteriaGuard/pulls](https://github.com/Saksham-official/CriteriaGuard/pulls) and click **New Pull Request**.
   - Ensure the PR template checklist is completed:
     - [ ] Code follows project standards and architectural guidelines.
     - [ ] `pre-commit run --all-files` passes cleanly.
     - [ ] Unit tests are added or updated, and `pytest` passes.
     - [ ] Documentation has been updated (if applicable).
     - [ ] No secrets or `.env` files are committed.
6. **Code Review**:
   - Maintainers will review your PR. Address feedback by pushing additional commits to your branch.
   - Once approved, your PR will be squash-merged into `main`.

---

## 📐 Coding Standards

### Python & FastAPI Standards

1. **Python 3.11+ Type Hints**:
   - All function signatures, return types, and class attributes must have explicit type hints:
     ```python
     def compute_verdict(
         criterion: dict[str, Any],
         extraction: dict[str, Any],
         is_tampered_source: bool = False
     ) -> dict[str, Any]:
     ```
2. **Pydantic v2 Models for Validation**:
   - Define and validate all request payloads, criteria schemas, and extraction results using Pydantic models (see `backend/models/criterion.py` and `backend/models/extraction.py`).
3. **Layered Architecture & Separation of Concerns**:
   - **`routers/`**: Handle HTTP/WebSocket request routing, parameter extraction, and status codes.
   - **`engines/`**: Core evaluation and extraction logic (`criteria_lens`, `doc_probe`, `verdict_core`, `security_shield`).
   - **`services/`**: External services, document parsing (`pdf_extractor`, `ocr`, `report_gen`).
   - **`models/`**: Pydantic models and schemas.
   - **`prompts/`**: Structured system and extraction prompts.
4. **Logging**:
   - Always use the centralized logger from `utils.logger` (`from utils.logger import logger`).
   - Do **NOT** use `print()` statements in production code.
5. **Deterministic Evaluation Guarantee**:
   - Never replace deterministic Boolean/numerical checks with LLM calls in `VerdictCore`.

---

### React & Frontend Standards

1. **Modern Functional Components**:
   - Use functional components with React Hooks.
   - Follow ESLint React Hooks rules (`eslint-plugin-react-hooks`).
2. **Design Language**:
   - Adhere to the established **Glassmorphism & High-Integrity Governance** theme.
   - Use Tailwind CSS utility classes with clean hierarchy.
   - Ensure accessibility and responsiveness across screen sizes.
3. **Component Hygiene**:
   - Deconstruct complex dashboards into focused, reusable components.
   - Ensure clear prop typing and meaningful variable names.

---

### Security & Anti-Tampering Standards

1. **Zero Secret Leakage**:
   - Never commit API keys (`GROQ_API_KEY`, `SUPABASE_SERVICE_KEY`, etc.), credentials, or `.env` files.
   - Our `.gitignore` is pre-configured to ignore `.env`, `.env.*`, `uploads/`, and temporary directories.
2. **Adversarial Input Sanitization**:
   - Bidders submit untrusted PDFs. Any new document ingestion pipeline must pass through `SecurityShield` to guard against hidden text injection layers and forged EXIF data.
3. **Audit Immutability**:
   - Any database operations affecting tenders, bidders, or verdicts must record an event with SHA-256 hash chaining to maintain tamper evidence.

---

## 💬 Reporting Issues & Getting Help

- **Found a Bug?** Open an issue on GitHub: [CriteriaGuard Issues](https://github.com/Saksham-official/CriteriaGuard/issues). Please include:
  - Clear steps to reproduce the bug.
  - Expected vs. actual behavior.
  - System environment (OS, Python version, Node.js version).
  - Relevant logs or stack traces.
- **Have a Feature Idea?** We welcome discussions! Please open an issue labeled `enhancement` outlining the problem, proposed solution, and governance implications.
- **Security Vulnerabilities**: If you discover a security vulnerability, please report it privately to the repository maintainers rather than opening a public issue.

---

*Thank you for helping build accountable, transparent, and explainable AI for public governance!* 🛡️
