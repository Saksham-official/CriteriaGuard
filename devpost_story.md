# CriteriaGuard — DevPost Submission Story

---

## Inspiration

The spark came from a deceptively mundane fact: **every year, procurement committees across India spend days doing something a spreadsheet *should* handle — but can't**.

Reading through the CRPF problem statement, one sentence stopped us cold:

> *"Two evaluators may reach different conclusions from the same set of documents."*

That is not a technology failure. That is a **governance failure** — and it happens thousands of times a year across tenders worth hundreds of crores. A missed ISO certificate. A misread turnover figure on a scanned page. An ambiguous "shall" vs. "should" clause that one officer reads as mandatory and another doesn't. Each of these can flip a ₹50 crore contract, invite an RTI inquiry, or trigger a court challenge.

What inspired us most was the realisation that this problem had a *shape* — a clear input (tender + bids), a clear output (eligible / not eligible / needs review), and a clear integrity requirement (every decision must be traceable). It was not a vague "use AI to improve government" ask. It was a **surgical problem with a surgical solution space**.

The second source of inspiration was the failure mode of naive AI solutions. Every generic LLM wrapper *could* read a PDF and return a verdict — but it would hallucinate evidence, silently disqualify borderline candidates, and produce nothing you could put in front of a judge. We were inspired to build the system that a procurement officer could actually **trust their name on**.

---

## What It Does

CriteriaGuard is a three-stage pipeline — **CriteriaLens → DocProbe → VerdictCore** — that transforms a tender document and a set of bidder submissions into a signed, audit-ready evaluation report.

### Stage 1 — CriteriaLens (Tender Intelligence)

The officer uploads the tender document. CriteriaLens (powered by Llama 3.3 70B via Groq at `temperature=0`) extracts every eligibility criterion into a formal schema:

$$\text{Criterion} = \{\text{type}, \text{text}, \text{threshold}, \text{unit}, \text{mandatory\_flag}, \text{mandatory\_confidence}\}$$

Crucially, it performs **linguistic marker analysis** — distinguishing "shall" and "must" (mandatory) from "should" and "preferred" (optional). Any criterion where the language is ambiguous is flagged with `mandatory_confidence: ambiguous` and routed to an **Officer Checkpoint** before evaluation begins. This is where most systems stop; we built the checkpoint in because skipping it means the entire downstream evaluation rests on an assumption nobody verified.

### Stage 2 — DocProbe (Bidder Understanding)

Each bidder's submission is processed through a multi-format pipeline. Typed PDFs go through `pdfplumber` (layout-preserving extraction). Scanned documents and photographs go through a **Tesseract + Google Cloud Vision ensemble**, with automatic quality scoring. Word documents are converted inline. The extraction anchors every value to its source: document name, page number, and a verbatim excerpt (≤ 80 words).

$$\text{Confidence} = f(\underbrace{\text{OCR quality}}_{\alpha}, \underbrace{\text{value alignment}}_{\beta}, \underbrace{\text{authenticity}}_{\gamma}, \underbrace{\text{parseability}}_{\delta})$$

Low-confidence extractions are never silently discarded. They are tagged with a `not_found_reason` enum (`document_missing | value_unreadable | not_stated`) and queued for human review.

### Stage 3 — VerdictCore (Explainable Verdicts)

This is the part we are most proud of. **No LLM touches the final verdict.** VerdictCore is pure deterministic Python:

- A value above threshold → `ELIGIBLE`  
- A value below threshold → `NOT_ELIGIBLE`  
- A value within **10% of the threshold** → `BORDERLINE` (flagged for review, not auto-rejected)  
- An unreadable or missing value → `NEEDS_REVIEW` with the explicit reason

The 10% borderline rule, for example, catches the case in the PS sample scenario: Kumar Ltd with ₹4.6 Cr turnover against a ₹5 Cr requirement — a difference of ₹40 lakh that arguably deserves a human eye, not an automatic rejection.

Every verdict is backed by the SHA-256 chained audit trail — append-only, tamper-evident, verifiable in one click.

---

## How We Built It

The stack was chosen for **auditability at every layer**, not just performance.

| Layer | Technology | Reason |
|---|---|---|
| Backend | FastAPI + Pydantic v2 | Strict schema validation; every API response is typed and verified |
| LLM | Llama 3.3 70B via Groq | `temperature=0` for deterministic extraction; Groq's speed matters for real-time pipeline feedback |
| OCR | Tesseract + Cloud Vision | Ensemble approach — Vision for quality, Tesseract as fallback with confidence scoring |
| Database | PostgreSQL (Supabase) | SHA-256 chained audit log stored as append-only rows |
| Frontend | React 18 (Vite) + custom glassmorphism UI | Desktop-optimised; the Evaluation Matrix is information-dense by design |
| PDF Reports | ReportLab | Generates signed, formatted audit-ready reports on demand |

The build process was deliberately sequential — we established the schema first (Pydantic models define the contract between all stages), then built CriteriaLens, then DocProbe, then VerdictCore, and finally wired the frontend to surface every internal state that a judge or officer would care about.

One architectural decision we made early and never regretted: **the UI must expose the pipeline**. The frontend shows which engine processed each document (`pdfplumber (digital)` vs. `Google Vision OCR (scanned)` vs. `Tesseract fallback`). The audit trail is a first-class screen, not a log file buried in a menu. The confidence breakdown is visible per extraction, not collapsed into a single opaque score.

---

## Challenges We Ran Into

**1. The hallucination boundary**

The hardest design question was: *where does the LLM stop and deterministic logic begin?* Too far left (LLM decides verdicts) → hallucination risk. Too far right (LLM only does trivial extraction) → you've wasted the model's capability. We drew the line at extraction: the LLM reads and retrieves, Python evaluates and decides. Enforcing this boundary in code took discipline — every time a "smart" shortcut appeared, we asked whether it moved the verdict decision into the model.

**2. Groq API rate limits and model deprecations mid-build**

During development, we hit Groq's TPM (tokens-per-minute) limits on the Llama 3.3 70B endpoint, and one model alias was deprecated without notice. This forced us to build a **model fallback chain** with retry logic and exponential backoff, and to refactor the extraction prompts to be significantly more token-efficient without losing structured output fidelity. The Pydantic retry cycle — `Attempt 1 → validation fail → Attempt 2 → success / flag low-confidence` — was born from this pain.

**3. OCR confidence calibration**

Making the OCR quality score *meaningful* rather than theatrical was harder than expected. A confidence score of 0.6 means nothing to a procurement officer. What matters is whether the specific field — the rupee figure in the turnover certificate — was read cleanly. We had to build field-level confidence rather than document-level confidence, which required anchoring the OCR output back to the schema fields before scoring.

**4. The "mandatory vs. optional" ambiguity problem**

Tender language is written by lawyers, not engineers. Phrases like "the bidder is expected to have..." or "preference will be given to..." don't map cleanly to boolean mandatory flags. We built an Ambiguity Resolver that produces a structured analysis (`likely_mandatory`, `reasoning`, `similar_criterion_pattern`) but routes the final call to the officer. Getting the resolver's output to be *useful* rather than just hedged required several prompt iterations and a small set of real tender language examples as few-shot inputs.

**5. Building an audit trail that is actually tamper-evident**

An audit trail that is only logged, not chained, is cosmetic. We implemented SHA-256 block chaining:

$$H_n = \text{SHA-256}(\text{data}_n \| H_{n-1})$$

where $H_0$ is a genesis hash. Any modification to a historical record breaks all subsequent hashes, and the integrity check button verifies the full chain in $O(n)$ time. The challenge was handling the dual timestamp format from different log sources — legacy records used a different precision, which caused false-positive integrity failures until we implemented a normalisation layer before hashing.

---

## Accomplishments That We're Proud Of

- **Zero-hallucination verdict architecture.** The final ELIGIBLE/NOT\_ELIGIBLE/NEEDS\_REVIEW decision is made by deterministic Python code, not by the LLM. Every verdict can be reproduced identically given the same inputs.

- **The borderline detection system.** The 10% threshold flag is a small feature with outsized governance value — it transforms what would be a silent rejection into a human-reviewable borderline case. In the sample scenario, this is exactly what saves Kumar Ltd from automatic disqualification on ₹40 lakh of headroom.

- **The Officer Review Queue before evaluation starts.** Most teams build systems that evaluate first and surface problems later. We built the checkpoint *before* evaluation — ambiguous criteria must be resolved by the officer before a single bidder is scored. This is the correct order for a formal procurement process and, apparently, something most solutions skip.

- **A complete, navigable UI that exposes every internal state.** The Evaluation Matrix (bidders × criteria with verdict badges), the Evidence Drawer (slide-out with verbatim excerpt + confidence breakdown), the Audit Trail screen (SHA-256 chain with integrity button), the Override flow (officer must type a reason, which is then logged) — all of it is built and working.

- **The demo scenario matches the PS exactly.** 6 eligible, 3 not eligible, 1 flagged for review (OCR failure on turnover figure). The problem statement literally wrote out the success criteria — we built to it.

---

## What We Learned

**Architecture is a policy decision, not just a technical one.** Every choice about where to put the LLM, where to put the deterministic logic, and what to surface in the UI carries a governance implication. We learned to ask "what does the procurement officer need to sign their name on this?" for every design decision.

**Explainability is not a feature, it is a constraint.** When you build a system where every verdict must trace back to a source document, page number, and verbatim excerpt, the system architecture changes. You cannot afford to discard intermediate outputs. You cannot summarise evidence — you must quote it. This constraint made every component harder to build and the final product dramatically more trustworthy.

**Confidence scoring needs to be field-level, not document-level.** A document can be high-quality overall but have one unreadable figure — and that figure might be the exact thing you need. Document-level OCR scores are misleading. Field-anchored confidence scores are what actually matter.

**Rate limits are a systems design problem, not a devops problem.** Groq TPM limits are not something you route around with retries alone. You redesign prompts to be more token-efficient, you batch intelligently, and you build fallback chains. The constraint forced better engineering.

**The human-in-the-loop path is the product.** The AI parts of CriteriaGuard are impressive but replicable. The officer review queue, the override logging, the ambiguity resolver — these are the parts that make the system *governable*, which is what actually matters for a formal procurement context.

---

## What's Next for CriteriaGuard

**Short term (Round 2 readiness):**
- Run the full pipeline on CRPF's representative mock tender and bidder documents inside the provided sandbox.
- Fine-tune the linguistic marker analysis on real government tender language (GeM, CPWD, defence procurement) to improve `mandatory_confidence` accuracy.
- Harden the OCR confidence calibration with field-level scoring validated against known-good extractions.

**Medium term:**
- **Multi-tender support** — parallel evaluation across multiple active tenders with a unified Review Queue.
- **Learning from overrides** — officer override decisions, with reasons, form a feedback corpus that can improve extraction accuracy over time without retraining the base model.
- **GeM integration** — pull tender metadata directly from the Government e-Marketplace API to pre-populate the criteria schema and reduce manual upload friction.

**Governance roadmap:**
- **NIC/MeitY deployment readiness** — the Docker-containerised backend is already structured for sovereign infrastructure deployment. The next step is hardening it against NIC's security baseline and producing a formal data-handling specification.
- **Digital signature chain** — replace the officer "signature block" in the PDF report with a proper PKI-backed digital signature, making the report legally equivalent to a manually signed evaluation sheet.
- **RTI-ready audit export** — a one-click export of the complete audit trail for a given tender, formatted and time-stamped for RTI (Right to Information) responses.

The long-term vision is a system that sits quietly *behind* the existing procurement process — invisible to the public, indispensable to the officer — making every evaluation faster, every decision traceable, and every challenge to a procurement outcome answerable with a complete evidence trail.

---

*"Built for the realities of Indian Government Procurement — where accountability meets intelligence."* 🛡️
