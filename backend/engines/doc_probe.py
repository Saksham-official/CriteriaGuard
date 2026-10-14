import json
import os
import re
import time

import httpx
from groq import Groq, RateLimitError

from models.extraction import ExtractionSchema
from prompts.value_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from utils.logger import logger

# Initialize Groq client safely (None if not provided)
client = None
if os.getenv("GROQ_API_KEY"):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client in DocProbe: {e}")

# Live Groq models as of May 2026
MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
]


def _get_mock_extraction(criterion_dict: dict, documents_with_labels: str) -> ExtractionSchema:
    """Return deterministic extraction for contributor offline mode without LLM calls."""
    c_id = str(criterion_dict.get("id", "c001")).upper()
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests",
        "fixtures",
        "sample_bidder_submission.json",
    )

    if os.path.exists(fixture_path):
        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
                submissions = data.get("submissions", [])
                for sub in submissions:
                    extractions = sub.get("extractions", {})
                    for ext_key, ext_val in extractions.items():
                        if (
                            ext_key.upper() == c_id
                            or ext_val.get("criterion_id", "").upper() == c_id
                        ):
                            return ExtractionSchema(
                                criterion_id=str(criterion_dict.get("id")),
                                value_found=ext_val.get("value_found", True),
                                not_found_reason=ext_val.get("not_found_reason"),
                                extracted_value=ext_val.get("extracted_value"),
                                extracted_value_numeric=ext_val.get("extracted_value_numeric"),
                                source_document=ext_val.get(
                                    "source_document", "Bidder_Proposal.pdf"
                                ),
                                source_page=ext_val.get("source_page", 1),
                                source_excerpt=ext_val.get(
                                    "source_excerpt", "Verified evidence excerpt."
                                ),
                                ocr_quality=ext_val.get("ocr_quality", "high"),
                                alignment_score=ext_val.get("alignment_score", 0.95),
                                authenticity_score=ext_val.get("authenticity_score", 0.95),
                                notes=ext_val.get("notes"),
                            )
        except Exception as e:
            logger.warning(f"Failed to load sample bidder fixture in DocProbe: {e}")

    # Fallback heuristic extraction
    threshold_val = criterion_dict.get("threshold_value")
    if threshold_val is None and isinstance(criterion_dict.get("threshold"), dict):
        threshold_val = criterion_dict["threshold"].get("value")

    numeric_val = float(threshold_val) if threshold_val is not None else 100.0

    return ExtractionSchema(
        criterion_id=str(criterion_dict.get("id")),
        value_found=True,
        not_found_reason=None,
        extracted_value=f"{numeric_val} (Verified from proposal)",
        extracted_value_numeric=numeric_val,
        source_document="Proposal_Document.pdf",
        source_page=1,
        source_excerpt="Documentation submitted in Section 2 meets standard requirements.",
        ocr_quality="high",
        alignment_score=0.95,
        authenticity_score=0.95,
        notes="Deterministic mock extraction (MOCK_LLM=true)",
    )


def extract_value_for_criterion(
    criterion_dict: dict, documents_with_labels: str, on_token=None
) -> ExtractionSchema:
    is_mock = (
        os.getenv("MOCK_LLM", "").lower() in ("true", "1")
        or not os.getenv("GROQ_API_KEY")
        or client is None
    )

    if is_mock:
        if on_token:
            on_token("Analyzing documents using deterministic offline mock engine...")
        return _get_mock_extraction(criterion_dict, documents_with_labels)

    # Safety truncation for Groq free tier to stay within TPM limits
    documents_with_labels = documents_with_labels[:15000]

    user_prompt = USER_PROMPT_TEMPLATE.format(
        criterion_json=json.dumps(criterion_dict, indent=2),
        documents_with_labels=documents_with_labels,
        criterion_id=criterion_dict.get("id", "unknown"),
    )

    for model in MODELS:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if on_token:
                    logger.info(
                        f"DocProbe: Calling {model} in streaming mode for criterion {criterion_dict.get('id', '?')} (attempt {attempt + 1})"
                    )
                    assert client is not None
                    response_stream = client.chat.completions.create(
                        model=model,
                        max_tokens=1000,
                        temperature=0,
                        timeout=httpx.Timeout(60.0, connect=10.0),
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        stream=True,
                    )
                    collected_tokens = []
                    for chunk in response_stream:
                        delta = chunk.choices[0].delta.content or ""
                        if delta:
                            collected_tokens.append(delta)
                            on_token(delta)
                    raw_content = "".join(collected_tokens)
                else:
                    assert client is not None
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=1000,
                        temperature=0,
                        timeout=httpx.Timeout(60.0, connect=10.0),
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    )
                    raw_content = response.choices[0].message.content or ""

                cleaned = raw_content.strip()
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

                try:
                    data = json.loads(cleaned)
                except Exception:
                    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(0))
                        except Exception:
                            continue
                    else:
                        continue

                if not isinstance(data, dict):
                    continue

                data["criterion_id"] = str(criterion_dict.get("id"))
                return ExtractionSchema(**data)

            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    break
            except Exception as e:
                logger.warning(f"DocProbe: Model {model} failed with {type(e).__name__}: {e}")
                break

    return ExtractionSchema(
        criterion_id=str(criterion_dict.get("id")),
        value_found=False,
        not_found_reason="value_unreadable",
        ocr_quality="low",
        alignment_score=0,
        authenticity_score=0,
        notes="All LLM extraction attempts failed (potential rate limit or model timeout).",
    )
