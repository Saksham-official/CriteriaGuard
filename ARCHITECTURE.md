# 🏗️ ARCHITECTURE.md — CriteriaGuard System Architecture

## Architecture Philosophy

Three principles drive every design decision:

1. **Evidence-first** — No verdict without a traceable source. Every extraction must cite document + page + excerpt or return explicit `not_found`.
2. **Fail safe, not fail silent** — When confidence is low, route to human review. Never auto-decide on uncertain data.
3. **Officer in the loop** — The AI recommends. The officer decides. Every override is logged.

---

## High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CRITERAGUARD PLATFORM                       │
│                                                                     │
│  ┌──────────┐     ┌─────────────────────────────────────────────┐  │
│  │ Officer  │────▶│              REACT FRONTEND                  │  │
│  │  (User)  │◀────│  Upload │ Review │ Dashboard │ Audit Trail  │  │
│  └──────────┘     └─────────────────┬───────────────────────────┘  │
│                                     │ REST API                      │
│                   ┌─────────────────▼───────────────────────────┐  │
│                   │              FASTAPI BACKEND                  │  │
│                   │                                               │  │
│                   │  ┌───────────┐ ┌──────────┐ ┌────────────┐  │  │
│                   │  │CriteriaLen│ │ DocProbe │ │VerdictCore │  │  │
│                   │  │  Engine 1 │ │ Engine 2 │ │  Engine 3  │  │  │
│                   │  └─────┬─────┘ └────┬─────┘ └─────┬──────┘  │  │
│                   │        │            │              │          │  │
│                   │  ┌─────▼────────────▼──────────────▼──────┐  │  │
│                   │  │           SERVICE LAYER                  │  │  │
│                   │  │  OCR │ PDF Parser │ Report Gen │ Audit  │  │  │
│                   │  └─────────────────────────────────────────┘  │  │
│                   └────────────────┬────────────────────────────┘  │
│                                    │                                │
│          ┌─────────────────────────┼──────────────────────┐        │
│          │                         │                       │        │
│  ┌───────▼──────┐  ┌───────────────▼──┐  ┌───────────────▼─────┐  │
│  │   Supabase   │  │  Claude Sonnet   │  │  Google Vision API  │  │
│  │  PostgreSQL  │  │   (Anthropic)    │  │   + Tesseract OCR   │  │
│  │  + Storage   │  │   Temperature=0  │  │   (local fallback)  │  │
│  └──────────────┘  └──────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Engine 1 — CriteriaLens

### Responsibility
Convert a raw tender PDF into a structured, officer-approved eligibility criteria schema.

### Pipeline

```
Tender PDF
    │
    ▼
┌─────────────────┐
│  PDF Extractor  │  pdfplumber → full text with page markers
│  (pdfplumber)   │  PyMuPDF → table detection + layout preservation
└────────┬────────┘
         │ raw_text (with page numbers)
         ▼
┌─────────────────┐
│  Text Chunker   │  Split by section headers (Regex + heuristics)
│                 │  Preserve clause numbers (e.g., "4.2(b)")
└────────┬────────┘
         │ chunks[]
         ▼
┌─────────────────┐
│  Claude Sonnet  │  System: procurement analyst persona
│  (Extraction)   │  Temp: 0 | Max tokens: 2000
│                 │  Output: strict JSON schema (see PROMPT_ENGINEERING.md)
└────────┬────────┘
         │ raw_criteria_json
         ▼
┌─────────────────┐
│ Pydantic        │  Validates every field
│ Validator       │  Rejects malformed responses → retry once → flag ambiguous
└────────┬────────┘
         │ CriterionSchema[]
         ▼
┌─────────────────┐
│ Officer Review  │  Ambiguous mandatory criteria → amber flag
│ UI              │  Officer edits/approves before evaluation begins
└────────┬────────┘
         │ approved_criteria[]
         ▼
    Supabase DB
```

### Mandatory vs Optional Classification

```python
MANDATORY_SIGNALS = ["shall", "must", "essential", "mandatory", "required", "compulsory"]
OPTIONAL_SIGNALS  = ["should", "preferred", "desirable", "may", "if available", "where applicable"]

def classify_mandatory(text: str) -> tuple[bool, str]:
    text_lower = text.lower()
    mandatory_hits = [s for s in MANDATORY_SIGNALS if s in text_lower]
    optional_hits  = [s for s in OPTIONAL_SIGNALS  if s in text_lower]

    if mandatory_hits and not optional_hits:
        return True, "high"
    elif optional_hits and not mandatory_hits:
        return False, "high"
    else:
        return True, "ambiguous"  # Flag for officer — never assume optional
```

---

## Engine 2 — DocProbe

### Responsibility
Parse every bidder document (any format) and extract the value relevant to each criterion, with a source citation.

### Document Routing

```
Uploaded File
      │
      ├──── .pdf ──► Is it scanned?
      │                  │
      │          ┌───────┴──────────┐
      │          │ text_ratio < 0.1 │ (scanned)
      │          YES                NO
      │          │                  │
      │          ▼                  ▼
      │    Image Pipeline      pdfplumber
      │    (see below)         Direct Extraction
      │
      ├──── .docx ──► python-docx → plain text
      │
      ├──── .jpg/.png/.tiff ──► Image Pipeline
      │
      └──── unknown ──► Explicit error → NEEDS_REVIEW

Image Pipeline:
    Raw Image
        │
        ▼
    Pillow Preprocessor
        ├── Deskew (rotation correction)
        ├── Contrast enhancement (CLAHE)
        ├── Noise removal (median filter)
        └── Binarisation (adaptive threshold)
        │
        ▼
    Google Vision OCR ──► confidence score returned
        │
        ├── confidence ≥ 0.80 ──► Use Vision result
        └── confidence < 0.80 ──► Run Tesseract locally
                                      │
                                      └── Take higher confidence result
```

### Extraction per Criterion

For each `(criterion, bidder)` pair:

```python
async def extract_value(criterion: CriterionSchema, doc_pages: list[DocPage]) -> Extraction:

    # Build context window — include only pages likely to contain this criterion type
    relevant_pages = filter_by_criterion_type(doc_pages, criterion.category)
    context = format_pages_with_labels(relevant_pages)  # "[Balance_Sheet.pdf, p.4]: ..."

    # Call Claude with extraction prompt (see PROMPT_ENGINEERING.md)
    response = await claude_client.extract(criterion, context)

    # Validate
    extraction = ExtractionSchema.model_validate(response)

    # Hard rule: no evidence without source
    if extraction.value_found and not extraction.source_document:
        extraction.value_found = False
        extraction.not_found_reason = "extraction_without_citation_rejected"

    return extraction
```

### Confidence Factors

```python
def compute_confidence(extraction: Extraction, ocr_quality: str) -> float:
    scores = {
        "ocr_quality":      {"high": 1.0, "medium": 0.7, "low": 0.4}[ocr_quality],
        "value_alignment":  extraction.alignment_score,      # from Claude
        "doc_authenticity": extraction.authenticity_score,   # from Claude
        "parseability":     1.0 if extraction.numeric_value else 0.6
    }
    weights = [0.25, 0.35, 0.20, 0.20]
    return sum(s * w for s, w in zip(scores.values(), weights))
```

---

## Engine 3 — VerdictCore

### Responsibility
Given a criterion and an extraction, produce a verdict with a plain-English explanation. Pure deterministic Python — no LLM.

### Decision Tree

```python
def compute_verdict(criterion: CriterionSchema, extraction: Extraction) -> Verdict:

    # ── GATE 1: Evidence presence ──────────────────────────────────────
    if not extraction.value_found:
        if criterion.mandatory:
            return Verdict(
                status="NEEDS_REVIEW",
                reason=f"Mandatory document not found or unreadable: {extraction.not_found_reason}"
            )
        return Verdict(status="ELIGIBLE", reason="Optional criterion — document not required.")

    conf = extraction.confidence
    val  = extraction.extracted_value_numeric
    thr  = criterion.threshold.value if criterion.threshold else None

    # ── GATE 2: Confidence floor ───────────────────────────────────────
    if conf < 0.75:
        return Verdict(
            status="NEEDS_REVIEW",
            reason=f"Extraction confidence {conf:.0%} below threshold. OCR quality: {extraction.ocr_quality}. Officer must verify."
        )

    # ── GATE 3: Borderline numeric (within 10% of threshold) ──────────
    if thr and val and abs(val - thr) / thr < 0.10:
        return Verdict(
            status="NEEDS_REVIEW",
            reason=f"Borderline value {val} vs threshold {thr}. Within 10% margin — officer confirmation required."
        )

    # ── GATE 4: Clear numeric verdict ─────────────────────────────────
    if thr and val:
        op = criterion.threshold.comparison
        passed = (val >= thr if op == "greater_than_equal" else val == thr)
        src = f"{extraction.source_document}, page {extraction.source_page}"
        if passed:
            return Verdict(status="ELIGIBLE",     reason=f"Found {val} in {src}. Threshold {thr} met.")
        else:
            return Verdict(status="NOT_ELIGIBLE", reason=f"Required {thr}, found {val} in {src}.")

    # ── GATE 5: Non-numeric (boolean) criterion ────────────────────────
    return Verdict(
        status="ELIGIBLE",
        reason=f"Criterion satisfied. Evidence: {extraction.source_document}, page {extraction.source_page}."
    )
```

---

## Audit Trail — SHA-256 Chaining

Every action in the system appends an immutable entry. The chain works like a simplified blockchain:

```python
import hashlib, json
from datetime import datetime, timezone

def append_audit_entry(action_type: str, actor: str, target_id: str, result: str, metadata: dict):

    # Get previous hash (genesis entry uses "0" * 64)
    prev = db.get_latest_audit_entry()
    prev_hash = prev.entry_hash if prev else "0" * 64

    # Build entry content
    entry_content = {
        "sequence":    (prev.sequence + 1) if prev else 1,
        "action_type": action_type,
        "actor":       actor,
        "target_id":   target_id,
        "result":      result,
        "metadata":    metadata,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "previous_hash": prev_hash
    }

    # Hash
    entry_json = json.dumps(entry_content, sort_keys=True)
    entry_hash = "sha256:" + hashlib.sha256(entry_json.encode()).hexdigest()

    entry_content["entry_hash"] = entry_hash
    db.insert_audit_entry(entry_content)   # append-only — no UPDATE/DELETE on this table
    return entry_content


def verify_chain() -> tuple[bool, str]:
    entries = db.get_all_audit_entries_ordered()
    for i, entry in enumerate(entries):
        expected_prev = entries[i-1].entry_hash if i > 0 else "0" * 64
        recomputed = "sha256:" + hashlib.sha256(
            json.dumps({**entry.dict(exclude={"entry_hash"}), "previous_hash": expected_prev},
                       sort_keys=True).encode()
        ).hexdigest()
        if recomputed != entry.entry_hash:
            return False, f"Chain broken at sequence {entry.sequence}"
    return True, "Chain intact"
```

---

## Database Schema

```sql
-- Append-only audit log (no DELETE privilege granted on this table)
CREATE TABLE audit_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence     INTEGER NOT NULL UNIQUE,
    action_type  TEXT NOT NULL,
    actor        TEXT NOT NULL,
    target_type  TEXT,
    target_id    TEXT,
    result       TEXT,
    metadata     JSONB,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entry_hash   TEXT NOT NULL,
    previous_hash TEXT NOT NULL
);

CREATE TABLE tenders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'processing',  -- processing|criteria_review|evaluating|complete
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    locked_at    TIMESTAMPTZ,
    locked_by    TEXT
);

CREATE TABLE criteria (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id            UUID REFERENCES tenders(id),
    criterion_code       TEXT NOT NULL,              -- C001, C002...
    text                 TEXT NOT NULL,
    category             TEXT NOT NULL,              -- financial|technical|compliance|certification
    mandatory            BOOLEAN NOT NULL,
    mandatory_confidence TEXT NOT NULL DEFAULT 'high',
    threshold_value      NUMERIC,
    threshold_unit       TEXT,
    threshold_period     TEXT,
    threshold_comparison TEXT,
    evidence_documents   TEXT[],
    source_clause        TEXT,
    approved_by          TEXT,
    approved_at          TIMESTAMPTZ
);

CREATE TABLE bidders (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id  UUID REFERENCES tenders(id),
    name       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending'   -- pending|processing|complete
);

CREATE TABLE extractions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_id            UUID REFERENCES criteria(id),
    bidder_id               UUID REFERENCES bidders(id),
    value_found             BOOLEAN NOT NULL,
    not_found_reason        TEXT,
    extracted_value         TEXT,
    extracted_value_numeric NUMERIC,
    source_document         TEXT,
    source_page             INTEGER,
    source_excerpt          TEXT,
    ocr_quality             TEXT,
    extraction_confidence   NUMERIC,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE verdicts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_id    UUID REFERENCES criteria(id),
    bidder_id       UUID REFERENCES bidders(id),
    extraction_id   UUID REFERENCES extractions(id),
    status          TEXT NOT NULL,   -- ELIGIBLE|NOT_ELIGIBLE|NEEDS_REVIEW
    reason          TEXT NOT NULL,
    overridden_by   TEXT,
    override_action TEXT,
    override_reason TEXT,
    overridden_at   TIMESTAMPTZ,
    computed_at     TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Security Considerations

| Concern | Mitigation |
|---------|-----------|
| LLM prompt injection via documents | Bidder docs passed as data, never as system instructions. Pydantic validation rejects unexpected fields. |
| Fabricated evidence in LLM output | Hard rule: `value_found: true` requires non-null `source_document` + `source_page`. Violated extractions marked `not_found`. |
| Audit log tampering | SHA-256 chaining; no DELETE/UPDATE rights on `audit_log` table; verify endpoint exposed to officers |
| Document exfiltration | All processing server-side; documents stored in private Supabase Storage bucket |
| API key exposure | Keys in `.env`, excluded from git via `.gitignore`; Render secrets management for production |

---

## Performance Targets

| Operation | Target | How |
|-----------|--------|-----|
| Tender criteria extraction | < 45s for 80-page PDF | Async Claude call; chunked for large docs |
| Per-bidder per-criterion extraction | < 8s | Batched page context; parallel `asyncio.gather` |
| Full evaluation (10 bidders × 5 criteria) | < 8 minutes | Parallel bidder processing |
| PDF report generation | < 10s | WeasyPrint with pre-compiled template |
| Audit verification | < 2s | Sequential hash recomputation |
