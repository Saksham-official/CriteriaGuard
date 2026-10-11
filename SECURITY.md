# 🛡️ CriteriaGuard Security Policy

CriteriaGuard is a governance-grade AI platform engineered to evaluate Indian Government procurement and tender eligibility. Because this system is intended for public-sector audits, tender evaluation committees, and anti-corruption compliance, security and tamper-resistance are fundamental architectural requirements.

We take all security vulnerabilities seriously and appreciate the responsible disclosure of any issues.

---

## 🔒 Supported Versions

Only the latest release on the `main` branch is actively supported with security patches.

| Version / Branch | Supported          |
| ---------------- | ------------------ |
| `main`           | :white_check_mark: |
| `< 1.0.0`        | :x:                |

---

## 🎯 Scope of Security Policy

### What is In Scope:
1. **Deterministic Rule Integrity**: Flaws in `VerdictCore` or `backend/rules/` that could allow an ineligible bidder to be approved without triggering a "Needs Review" checkpoint or audit trail entry.
2. **Cryptographic Audit Chain Integrity**: Bypasses or collisions in the SHA-256 append-only hash chain (`backend/services/audit.py`), tampering with historical logs, or replay attacks.
3. **Multi-Tenant & Data Isolation**: Leaks of proprietary tender specifications, commercial bid details, or chartered accountant statements across unauthorized sessions or bidders.
4. **Adversarial Document Defenses & Anti-Tampering**: Evasion of PDF metadata tampering detection, prompt injections hidden in bidder PDFs, or OCR spoofing (`backend/engines/security_shield.py`).
5. **API & WebSocket Security**: Authentication/authorization flaws, unvalidated input injections, or denial-of-service on FastAPI endpoints and progress streaming.

### What is Out of Scope:
- Vulnerabilities dependent on root/physical access to an unhardened development workstation.
- Non-deterministic behavior in third-party LLMs (e.g., Llama 3 API quirks) that are properly caught and contained by our deterministic Python rules engine.
- Rate-limiting or quota exhaustion on free-tier external API keys.

---

## 📢 Reporting a Vulnerability

**Please DO NOT file public GitHub issues for security vulnerabilities.**

To report a security vulnerability responsibly:

1. **Email Private Disclosure**: Send an encrypted or confidential email to:
   - **`security@criteriaguard.org`** (or to repository maintainer **`saksham.official@outlook.com`**)
2. **Include Details**:
   - Title describing the vulnerability class (e.g. `[VULNERABILITY] Hash-chain collision in audit logging`).
   - Detailed description and threat model.
   - Step-by-step reproduction instructions or proof-of-concept (POC) script.
   - Potential impact on procurement evaluation.
3. **Private Advisory**: Alternatively, you can use GitHub's private vulnerability reporting feature directly under the **Security > Advisories** tab on GitHub:
   - [Submit a private security advisory](https://github.com/Saksham-official/CriteriaGuard/security/advisories/new)

---

## ⏱️ Response Timeline

- **Initial Acknowledgment**: Within **48 hours** of receiving your report.
- **Triage & Assessment**: Within **5 business days**, detailing confirmed severity and reproduction.
- **Fix & Patch Timeline**: Critical vulnerabilities are patched within **14 days**.
- **Public Disclosure**: Coordinated disclosure will occur only after the fix has been merged into `main` and verified.

---

## 🏆 Bug Bounty & Contributor Recognition

While CriteriaGuard is an open-source civic-technology initiative without large cash bounties, contributors who responsibly report verified security vulnerabilities will be:
- Publicly credited in our release notes and `SECURITY.md` Wall of Fame (unless you wish to remain anonymous).
- Awarded the **Security Champion** badge in our community hall of contributors.
