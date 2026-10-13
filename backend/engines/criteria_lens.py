import json
import os
import re
import time

from groq import Groq, RateLimitError
from pydantic import ValidationError

from models.criterion import CriterionSchema
from prompts.criteria_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from utils.logger import logger

# Initialize Groq client safely (None if not provided)
client = None
if os.getenv("GROQ_API_KEY"):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client: {e}")


def _coerce_criterion(item: dict) -> CriterionSchema | None:
    """
    Try to coerce a raw dict from the LLM into a CriterionSchema,
    applying best-effort type fixes before strict validation.
    """
    # Fix source_page: LLM sometimes returns a string like "1" or null
    if "source_page" in item:
        try:
            item["source_page"] = int(item["source_page"]) if item["source_page"] is not None else 1
        except (ValueError, TypeError):
            item["source_page"] = 1

    # Fix threshold: LLM sometimes returns the string "null" instead of JSON null
    if isinstance(item.get("threshold"), str):
        item["threshold"] = None

    # Fix threshold value: LLM sometimes returns a string number
    if isinstance(item.get("threshold"), dict) and item["threshold"]:
        t = item["threshold"]
        if isinstance(t.get("value"), str):
            try:
                t["value"] = float(t["value"])
            except (ValueError, TypeError):
                t["value"] = None
        # Fix unit/period/comparison: LLM sometimes returns "null" string
        for key in ("unit", "period", "comparison"):
            if t.get(key) == "null":
                t[key] = None

    # Fix evidence_documents: LLM sometimes returns a string instead of list
    if isinstance(item.get("evidence_documents"), str):
        item["evidence_documents"] = [item["evidence_documents"]]
    if item.get("evidence_documents") is None:
        item["evidence_documents"] = []

    # Fix mandatory: LLM sometimes returns "true"/"false" strings
    if isinstance(item.get("mandatory"), str):
        item["mandatory"] = item["mandatory"].lower() == "true"

    # Fix mandatory_confidence: ensure it's one of the valid values
    if item.get("mandatory_confidence") not in ("high", "ambiguous"):
        item["mandatory_confidence"] = "ambiguous"

    try:
        return CriterionSchema(**item)
    except ValidationError as ve:
        logger.warning(f"ValidationError for criterion id={item.get('id', '?')}: {ve}")
        return None


def _get_mock_criteria(tender_text: str) -> list[CriterionSchema]:
    """Return deterministic criteria from fixture or fallback for offline development."""
    logger.info("Using deterministic mock extraction (MOCK_LLM=true / offline mode)")
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests",
        "fixtures",
        "sample_tender.json",
    )
    if os.path.exists(fixture_path):
        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
                return [CriterionSchema(**c) for c in data.get("criteria", [])]
        except Exception as e:
            logger.warning(f"Could not load sample_tender.json fixture: {e}")

    # Fallback criteria
    fallback = [
        {
            "id": "C001",
            "text": "The bidder shall have an average annual turnover of at least 50 Crores INR over the last three financial years.",
            "category": "financial",
            "mandatory": True,
            "mandatory_confidence": "high",
            "threshold": {
                "value": 50.0,
                "unit": "crore",
                "period": "last_3_years",
                "comparison": "greater_than_equal",
            },
            "evidence_documents": ["Audited Balance Sheets"],
            "source_clause": "Clause 4.1",
            "source_page": 1,
        },
        {
            "id": "C002",
            "text": "The bidder must possess a valid ISO 9001:2015 certification.",
            "category": "compliance",
            "mandatory": True,
            "mandatory_confidence": "high",
            "threshold": None,
            "evidence_documents": ["ISO Certificate"],
            "source_clause": "Clause 4.3",
            "source_page": 2,
        },
    ]
    return [CriterionSchema(**c) for c in fallback]


def extract_criteria_from_text(tender_text: str) -> list[CriterionSchema]:
    """
    Extract eligibility criteria from tender text using Groq LLM,
    or deterministic mock engine if MOCK_LLM is enabled or no API key is present.
    """
    is_mock = (
        os.getenv("MOCK_LLM", "").lower() in ("true", "1")
        or not os.getenv("GROQ_API_KEY")
        or client is None
    )
    if is_mock:
        return _get_mock_criteria(tender_text)

    SINGLE_CALL_LIMIT = 12_000
    MODELS = [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.3-70b-versatile",
        "qwen/qwen3-32b",
        "llama-3.1-8b-instant",
    ]

    all_criteria: list[CriterionSchema] = []
    seen_codes: set = set()

    def _call_llm(text_chunk: str, chunk_label: str) -> list[CriterionSchema]:
        """Call Groq LLM for a single chunk, trying each model with retries."""
        user_prompt = USER_PROMPT_TEMPLATE.format(tender_text=text_chunk)
        chunk_criteria: list[CriterionSchema] = []

        all_rate_limited = True
        for model in MODELS:
            max_retries = 2
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"[{chunk_label}] Calling Groq model={model}, attempt={attempt + 1}..."
                    )
                    assert client is not None
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=4000,
                    )
                    all_rate_limited = False

                    raw_content = response.choices[0].message.content or ""
                    cleaned = raw_content.strip()
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)

                    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
                    if match:
                        cleaned = match.group(0)

                    try:
                        parsed = json.loads(cleaned)
                    except json.JSONDecodeError as jde:
                        logger.warning(f"[{chunk_label}] JSON parse error from {model}: {jde}")
                        continue

                    if not isinstance(parsed, list):
                        logger.warning(
                            f"[{chunk_label}] Expected JSON list from {model}, got {type(parsed)}"
                        )
                        continue

                    added = 0
                    for item in parsed:
                        if not isinstance(item, dict):
                            continue
                        obj = _coerce_criterion(item)
                        if obj is not None and obj.id not in seen_codes:
                            chunk_criteria.append(obj)
                            seen_codes.add(obj.id)
                            added += 1

                    logger.info(f"[{chunk_label}] ({model}): extracted {added} criteria.")
                    return chunk_criteria

                except RateLimitError:
                    logger.warning(f"[{chunk_label}] {model} rate limited.")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2**attempt))
                    else:
                        break
                except Exception as e:
                    all_rate_limited = False
                    logger.error(f"[{chunk_label}] Error with {model}: {e}")
                    break

        if all_rate_limited:
            raise Exception(
                "All Groq models are currently rate-limited. Please try again in a few minutes."
            )

        return chunk_criteria

    if len(tender_text) <= SINGLE_CALL_LIMIT:
        all_criteria = _call_llm(tender_text, "FULL")
    else:
        chunk_size = 10_000
        chunks = [tender_text[i : i + chunk_size] for i in range(0, len(tender_text), chunk_size)]
        logger.info(f"Splitting into {len(chunks)} chunks of {chunk_size} chars.")
        for i, chunk in enumerate(chunks):
            if i > 0:
                time.sleep(5)
            all_criteria.extend(_call_llm(chunk, f"CHUNK {i + 1}/{len(chunks)}"))

    logger.info(f"Total criteria extracted: {len(all_criteria)}")
    return all_criteria
