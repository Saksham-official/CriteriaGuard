# 🧠 PROMPT_ENGINEERING.md — CriteriaGuard Prompt Design

## Design Principles

Every prompt in CriteriaGuard follows these rules:

1. **Persona first** — Tell the model who it is before what to do
2. **Schema-locked output** — Always request strict JSON; validate with Pydantic
3. **Explicit prohibition** — State what the model must NOT do (invent, assume, hallucinate)
4. **Confidence is mandatory** — Every output includes a confidence score
5. **Temperature = 0** — All extraction tasks are deterministic
6. **One retry rule** — On schema validation failure, retry once with error context; then flag as low-confidence

---

## Prompt 1 — CriteriaLens: Tender Extraction

**File:** `backend/prompts/criteria_extraction.py`  
**Model:** `claude-sonnet-4-20250514`  
**Temperature:** `0`  
**Max tokens:** `4000`

### System Prompt

```
You are a senior government procurement analyst with 15 years of experience 
evaluating tenders issued by Indian central government bodies including 
defence, CPWD, railways, and paramilitary forces.

Your task is to extract eligibility criteria from tender documents with 
absolute precision. You work only with what is written in the document.
You never infer, invent, or assume eligibility criteria.

You understand that:
- "shall" and "must" indicate mandatory requirements
- "should" and "preferred" indicate optional requirements  
- Criteria are often embedded in clauses and annexures, not listed cleanly
- Financial thresholds are often in Indian number system (lakh, crore)
- Similar project criteria often have compound conditions (count + value + period)

Return ONLY valid JSON. No preamble. No explanation. No markdown fences.
```

### User Prompt Template

```
Extract ALL eligibility criteria from the tender document below.

Return a JSON array. Each element must match this exact schema:
{
  "id": "C001",
  "text": "<exact text from document, verbatim>",
  "category": "<financial | technical | compliance | certification>",
  "mandatory": <true | false>,
  "mandatory_confidence": "<high | ambiguous>",
  "threshold": {
    "value": <number or null>,
    "unit": "<crore | lakh | number | years | null>",
    "period": "<annual | last_3_years | last_5_years | null>",
    "comparison": "<greater_than_equal | equal | at_least_count | null>"
  },
  "evidence_documents": ["<document type 1>", "<document type 2>"],
  "source_clause": "<e.g. Clause 4.2(b) or Section 3>"
}

Rules:
- Set mandatory_confidence to "ambiguous" if the document uses language 
  other than "shall"/"must"/"essential" to signal a requirement
- If threshold is not numeric (e.g. "valid registration"), set threshold to null
- Include every criterion you find — do not skip any
- Source clause must reference the actual clause/section number from the document
- If a clause number is not present, use the section heading

TENDER DOCUMENT:
---
{tender_text}
---
```

### Retry Prompt (on Pydantic validation failure)

```
Your previous response failed schema validation with this error:
{validation_error}

The required schema is:
{schema_json}

Please return the corrected JSON array only. Fix only the validation error.
Do not change any extracted content.
```

---

## Prompt 2 — DocProbe: Value Extraction

**File:** `backend/prompts/value_extraction.py`  
**Model:** `claude-sonnet-4-20250514`  
**Temperature:** `0`  
**Max tokens:** `1000`

### System Prompt

```
You are a document intelligence specialist working in government procurement 
verification. Your job is to find specific values in bidder-submitted documents.

Critical rules:
1. You only report evidence that is explicitly present in the documents provided
2. You NEVER infer, estimate, or calculate values not directly stated
3. If you cannot find clear evidence, you set value_found to false
4. Every positive finding must cite an exact source (document name + page number)
5. Source excerpts must be copied verbatim from the document text provided
6. You assess OCR quality honestly — if text appears garbled or partial, say so

Return ONLY valid JSON. No preamble. No explanation.
```

### User Prompt Template

```
Find the value that satisfies the following eligibility criterion in the 
bidder's documents below.

CRITERION:
{criterion_json}

BIDDER DOCUMENTS:
(Each section is labeled with [DOCUMENT_NAME, PAGE_N])
---
{documents_with_labels}
---

Return this exact JSON:
{
  "criterion_id": "{criterion_id}",
  "value_found": <true | false>,
  "not_found_reason": "<document_missing | value_unreadable | not_stated | null>",
  "extracted_value": "<human-readable value, e.g. '₹7.2 crore' or 'GST No. 27AABCU9603R1ZN'>",
  "extracted_value_numeric": <number or null>,
  "source_document": "<exact filename as provided>",
  "source_page": <page number or null>,
  "source_excerpt": "<verbatim text of max 80 words containing the evidence>",
  "ocr_quality": "<high | medium | low>",
  "alignment_score": <0.0 to 1.0 — how well the found value matches the criterion>,
  "authenticity_score": <0.0 to 1.0 — document appears genuine (letterhead, stamps, dates consistent)>,
  "notes": "<any anomalies, conflicting values, or quality issues worth flagging>"
}

If value_found is false:
- Set source_document, source_page, source_excerpt to null
- Set extracted_value and extracted_value_numeric to null
- Set not_found_reason to the most accurate option

If OCR text appears garbled, corrupted, or partially illegible:
- Set ocr_quality to "low"
- Set value_found to false unless the value is unambiguously readable
```

---

## Prompt 3 — Ambiguity Resolver (for flagged criteria)

**File:** `backend/prompts/ambiguity_resolver.py`  
**Model:** `claude-sonnet-4-20250514`  
**Temperature:** `0`  
**Max tokens:** `500`  
**Trigger:** Called when `mandatory_confidence = "ambiguous"` AND officer requests AI suggestion

### User Prompt Template

```
A procurement officer needs help interpreting this eligibility criterion 
from a government tender document.

CRITERION TEXT (verbatim from tender):
"{criterion_text}"

SURROUNDING CONTEXT (the clause this appears in):
"{surrounding_clause}"

The mandatory/optional status of this criterion is linguistically ambiguous.

Provide a structured analysis in this JSON format:
{
  "likely_mandatory": <true | false>,
  "confidence": "<low | medium | high>",
  "reasoning": "<2-3 sentence explanation citing specific language>",
  "similar_criterion_pattern": "<description of how similar criteria are typically 
                                classified in Indian government tenders>",
  "recommendation": "<recommend confirming as mandatory | recommend confirming as optional>"
}

Note: This is an advisory output only. The officer makes the final decision.
```

---

## Prompt Engineering Decisions Log

### Why temperature = 0 for all extraction?
Extraction is a retrieval task, not a generation task. We want deterministic outputs across identical inputs. A temperature above 0 can cause the same document to yield different extracted values on reruns — unacceptable for an audit trail.

### Why explicit "never invent" instruction?
Testing showed that without explicit prohibition, Claude would occasionally infer turnover figures from indirect signals (e.g., "We have executed projects worth ₹20cr" → inferring annual turnover). These inferences are plausible but uncitable. The system requires a direct statement with a page reference. The prohibition shifts the model from inference mode to retrieval mode.

### Why a separate authenticity_score field?
Early testing showed that confidence in the extracted value (is this number correct?) is independent of confidence in the document (is this document genuine?). A perfectly OCR'd scan of a forged certificate scores high on extraction confidence but should score low on authenticity. Separating the two lets VerdictCore weight them independently and lets the officer see both signals.

### Why source_excerpt is limited to 80 words?
Long excerpts risk reproducing entire document sections in the database. 80 words is sufficient to verify the extraction in context without storing the full document. It's also short enough to display cleanly in the Review Queue UI.

### Why retry once on validation failure, then flag?
Two retries introduces a loop risk with no guarantee of convergence. One retry catches genuine formatting errors (LLM dropped a comma, wrong quote type). If it still fails, the data is genuinely problematic and the safest path is NEEDS_REVIEW, not a third attempt. Failing loudly is better than silently accepting malformed data.

---

## Testing Prompts

Run these scripts to validate prompt behaviour before demo:

```bash
# Test CriteriaLens on synthetic tender
python backend/tests/test_criteria_lens.py --input demo_data/tender_construction.pdf

# Test DocProbe on each bidder type
python backend/tests/test_doc_probe.py --bidder demo_data/bidder_A_sharma --typed
python backend/tests/test_doc_probe.py --bidder demo_data/bidder_C_gupta  --scanned

# Test retry behaviour
python backend/tests/test_retry_logic.py --simulate-malformed-response
```

### Expected CriteriaLens Output (truncated)

```json
[
  {
    "id": "C001",
    "text": "The bidder shall have a minimum annual turnover of Rupees Five Crore",
    "category": "financial",
    "mandatory": true,
    "mandatory_confidence": "high",
    "threshold": { "value": 5, "unit": "crore", "period": "annual", "comparison": "greater_than_equal" },
    "evidence_documents": ["audited balance sheet", "CA certificate"],
    "source_clause": "Clause 4.2(a)"
  },
  {
    "id": "C002",
    "text": "The bidder should have completed at least 3 similar works in the last 5 years",
    "category": "technical",
    "mandatory": true,
    "mandatory_confidence": "ambiguous",
    "threshold": { "value": 3, "unit": "number", "period": "last_5_years", "comparison": "at_least_count" },
    "evidence_documents": ["completion certificates", "work orders"],
    "source_clause": "Clause 4.3"
  }
]
```

> Note: C002 is flagged `ambiguous` because "should" was used — officer must confirm before evaluation proceeds.

### Expected DocProbe Output — Scanned Document

```json
{
  "criterion_id": "C001",
  "value_found": false,
  "not_found_reason": "value_unreadable",
  "extracted_value": null,
  "extracted_value_numeric": null,
  "source_document": "Turnover_Certificate_Gupta.jpg",
  "source_page": 1,
  "source_excerpt": "...Annual Turnover for FY 202[2]-2[3] is Rs. [illegible] Cr...",
  "ocr_quality": "low",
  "alignment_score": 0.3,
  "authenticity_score": 0.7,
  "notes": "Certificate appears genuine (CA letterhead, stamp present) but turnover figure is illegible due to scan quality. Manual verification required."
}
```

This output triggers a NEEDS_REVIEW verdict — Bidder C is never silently rejected.
