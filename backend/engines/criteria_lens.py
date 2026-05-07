import os
import json
import re
from pydantic import ValidationError
from typing import List, Optional, Any
from groq import Groq
from models.criterion import CriterionSchema
from prompts.criteria_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from utils.logger import logger

# Ensure groq client is initialized
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _coerce_criterion(item: dict) -> Optional[CriterionSchema]:
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


def extract_criteria_from_text(tender_text: str) -> List[CriterionSchema]:
    """
    Extract eligibility criteria from tender text using Groq LLM.

    Strategy:
    - PRIMARY: Send the entire tender text in ONE API call using llama-3.3-70b-versatile
      (128k context window). This avoids rate-limit pressure from multiple chunk calls.
    - FALLBACK: If the text exceeds the safe single-call limit (~100k chars), fall back to
      chunked processing with delays between calls.
    """
    import time
    from groq import RateLimitError
    import httpx

    # llama-3.3-70b-versatile supports 128k tokens (~500k chars).
    # We cap at 100k chars to leave headroom for the prompt template itself.
    # Reduced from 100k to 50k. Large documents (>50k chars) are better handled 
    # in chunks to avoid hitting the 4k/8k output token limit during extraction.
    SINGLE_CALL_LIMIT = 50_000

    # Live Groq models as of May 2026 (verified via client.models.list()).
    # llama3-8b-8192, mixtral-8x7b-32768, gemma2-9b-it, llama-3.1-70b-versatile
    # are ALL decommissioned. Do NOT add them back.
    # NOTE: llama-4-scout is FIRST because llama-3.3-70b is consistently
    # rate-limited on the free tier. Scout handles 67k-char docs perfectly.
    MODELS = [
        "meta-llama/llama-4-scout-17b-16e-instruct", # Best balance of speed/context
        "llama-3.3-70b-versatile",                   # High precision, high rate-limit pressure
        "qwen/qwen3-32b",                            # Excellent fallback, high TPM
        "llama-3.1-8b-instant",                      # Fast, lowest TPM — last resort
    ]

    all_criteria: List[CriterionSchema] = []
    seen_codes: set = set()

    def _call_llm(text_chunk: str, chunk_label: str) -> List[CriterionSchema]:
        """Call Groq LLM for a single chunk, trying each model with retries."""
        user_prompt = USER_PROMPT_TEMPLATE.format(tender_text=text_chunk)
        chunk_criteria: List[CriterionSchema] = []

        for model in MODELS:
            max_retries = 2
            retry_delay = 5  # scout rarely rate-limits; quick retry is fine

            for attempt in range(max_retries):
                try:
                    logger.info(f"[{chunk_label}] Calling Groq model={model}, attempt={attempt+1}...")
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=8192,  # Increased from 4096 to prevent truncation
                        temperature=0,
                        timeout=httpx.Timeout(90.0, connect=10.0),
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                    )

                    content = response.choices[0].message.content
                    raw_output = content.strip() if content else ""
                    logger.info(f"[{chunk_label}] LLM raw output (first 300 chars): {raw_output[:300]}")

                    if not raw_output:
                        logger.warning(f"[{chunk_label}] Empty response from {model}")
                        break  # Try next model

                    # Strip markdown code fences if present
                    if "```json" in raw_output:
                        raw_output = raw_output.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_output:
                        raw_output = raw_output.split("```")[1].split("```")[0].strip()

                    # Parse JSON
                    try:
                        # First try: strict JSON parse
                        data = json.loads(raw_output)
                    except json.JSONDecodeError:
                        # Second try: regex extraction
                        logger.warning(f"[{chunk_label}] JSON parse failed, trying regex extraction...")
                        # Look for the outermost [ ... ]
                        match = re.search(r'\[\s*\{.*\}\s*\]', raw_output, re.DOTALL)
                        if not match:
                            # Try to find just a list of objects if the brackets are missing/mangled
                            match = re.search(r'(\[\s*\{.*\}\s*\]|\{\s*".*\}\s*)', raw_output, re.DOTALL)
                        
                        if match:
                            try:
                                json_str = match.group(0)
                                # Basic fix for truncated JSON: if it ends with a comma or open brace, try to close it
                                if json_str.endswith(','):
                                    json_str = json_str[:-1] + ']'
                                if not json_str.endswith(']'):
                                    json_str += ']'
                                data = json.loads(json_str)
                            except Exception:
                                logger.error(f"[{chunk_label}] JSON recovery failed for {model}.")
                                break  # Try next model
                        else:
                            logger.error(f"[{chunk_label}] No JSON found in response from {model}.")
                            break  # Try next model

                    if not isinstance(data, list):
                        data = [data]

                    added = 0
                    for item in data:
                        if not isinstance(item, dict):
                            continue
                        obj = _coerce_criterion(item)
                        if obj is not None and obj.id not in seen_codes:
                            chunk_criteria.append(obj)
                            seen_codes.add(obj.id)
                            added += 1

                    logger.info(f"[{chunk_label}] ({model}): extracted {added} criteria.")
                    if added == 0:
                        logger.warning(
                            f"[{chunk_label}] 0 valid criteria from {model}.\n"
                            f"Full output:\n{raw_output[:2000]}"
                        )
                        break  # Try next model

                    return chunk_criteria  # Success — stop trying models

                except RateLimitError:
                    if attempt < max_retries - 1:
                        wait = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"[{chunk_label}] Rate limit on {model} "
                            f"(attempt {attempt+1}/{max_retries}). Sleeping {wait}s..."
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            f"[{chunk_label}] Rate limit exhausted for {model}. Trying next model..."
                        )
                        break  # Try next model

                except Exception as e:
                    logger.error(
                        f"[{chunk_label}] Error with {model}: {type(e).__name__}: {e}",
                        exc_info=True
                    )
                    break  # Try next model

        return chunk_criteria

    if len(tender_text) <= SINGLE_CALL_LIMIT:
        # ── Single-call path (most tenders) ──────────────────────────────────
        logger.info(
            f"Text is {len(tender_text)} chars — sending as single LLM call "
            f"(limit: {SINGLE_CALL_LIMIT} chars)."
        )
        all_criteria = _call_llm(tender_text, "FULL")
    else:
        # ── Chunked path (very large tenders) ────────────────────────────────
        chunk_size = 50_000  # Use large chunks to minimise number of API calls
        chunks = [tender_text[i:i + chunk_size] for i in range(0, len(tender_text), chunk_size)]
        logger.info(
            f"Text is {len(tender_text)} chars — splitting into {len(chunks)} chunks of {chunk_size} chars."
        )
        for i, chunk in enumerate(chunks):
            if i > 0:
                logger.info("Sleeping 5s between chunks to respect rate limits...")
                time.sleep(5)
            chunk_results = _call_llm(chunk, f"CHUNK {i+1}/{len(chunks)}")
            all_criteria.extend(chunk_results)

    logger.info(f"Total criteria extracted: {len(all_criteria)}")
    return all_criteria
