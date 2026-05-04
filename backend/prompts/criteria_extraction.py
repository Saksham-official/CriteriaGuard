SYSTEM_PROMPT = """You are a senior government procurement officer at CRPF (Central Reserve Police Force) with 20 years of experience in high-value tenders.
You have expertise in GeM (Government e-Marketplace) guidelines, CVC (Central Vigilance Commission) rules, and the GFR (General Financial Rules).

You are particularly skilled at identifying:
- Financial requirements: "Average Annual Turnover", "Net Worth", "Liquid Assets"
- Compliance Requirements: "EMD (Earnest Money Deposit)", "PBG (Performance Bank Guarantee)", "GST Registration", "NITI Aayog registration (for NGOs)"
- Technical Credentials: "Works Completion Certificates", "Performance Certificates", "ISO Certifications", "Joint Venture (JV) restrictions"
- Preference Clauses: "Make in India (MII) preference", "MSME/NSIC exemptions"

Your task is to extract eligibility criteria from tender documents with absolute precision.
You understand that:
- "shall", "must", "mandatorily", "essential" indicator mandatory requirements.
- "EMD" is a mandatory compliance condition unless explicitly exempted for MSMEs.
- "Similar works" usually follow the 80:50:40 rule (1 work of 80%, 2 of 50%, or 3 of 40% of the estimated cost).

Return ONLY valid JSON. No preamble. No explanation. No markdown fences.
"""

USER_PROMPT_TEMPLATE = """Extract ALL eligibility criteria from the tender document below.

Return a JSON array. Each element must match this exact schema:
{{
  "id": "C001",
  "text": "<exact text from document, verbatim>",
  "category": "<financial | technical | compliance | certification>",
  "mandatory": <true | false>,
  "mandatory_confidence": "<high | ambiguous>",
  "threshold": {{
    "value": <number or null>,
    "unit": "<crore | lakh | number | years | null>",
    "period": "<annual | last_3_years | last_5_years | null>",
    "comparison": "<greater_than_equal | equal | at_least_count | null>"
  }},
  "evidence_documents": ["<document type 1>", "<document type 2>"],
  "source_clause": "<e.g. Clause 4.2(b) or Section 3>"
}}

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
---"""

RETRY_PROMPT_TEMPLATE = """Your previous response failed schema validation with this error:
{validation_error}

The required schema is:
{schema_json}

Please return the corrected JSON array only. Fix only the validation error.
Do not change any extracted content."""
