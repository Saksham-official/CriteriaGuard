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
    - PRIMARY: Send chunks of the tender text to stay within TPM/context limits.
    - MODELS: Try robust models first, falling back to faster ones.
    """
    import time
    from groq import RateLimitError
    import httpx

    # Reduced from 50k to 15k to stay within free-tier TPM limits (often 6k-10k).
    # 15k chars is ~3.5k tokens. Plus prompt and max_tokens, it should fit in ~6k-7k tokens.
    SINGLE_CALL_LIMIT = 15_000

    # Live Groq models as of May 2026.
    MODELS = [
        "meta-llama/llama-4-scout-17b-16e-instruct", # Best balance of speed/context
        "llama-3.3-70b-versatile",                   # High precision
        "qwen/qwen3-32b",                            # Excellent fallback
        "llama-3.1-8b-instant",                      # Fast last resort
    ]

    all_criteria: List[CriterionSchema] = []
    seen_codes: set = set()

    def _call_llm(text_chunk: str, chunk_label: str) -> List[CriterionSchema]:
        """Call Groq LLM for a single chunk, trying each model with retries."""
        user_prompt = USER_PROMPT_TEMPLATE.format(tender_text=text_chunk)
        chunk_criteria: List[CriterionSchema] = []

        all_rate_limited = True
        for model in MODELS:
            max_retries = 2
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    logger.info(f"[{chunk_label}] Calling Groq model={model}, attempt={attempt+1}...")
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=2048,  # Reduced from 8192 to stay under TPM limits
                        temperature=0,
                        timeout=httpx.Timeout(90.0, connect=10.0),
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    all_rate_limited = False # At least one model responded

                    content = response.choices[0].message.content
                    raw_output = content.strip() if content else ""
                    logger.info(f"[{chunk_label}] LLM raw output (first 300 chars): {raw_output[:300]}")

                    if not raw_output:
                        logger.warning(f"[{chunk_label}] Empty response from {model}")
                        break  # Try next model

                    # Strip markdown code fences
                    if "```json" in raw_output:
                        raw_output = raw_output.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_output:
                        raw_output = raw_output.split("```")[1].split("```")[0].strip()

                    # Parse JSON
                    try:
                        data = json.loads(raw_output)
                    except json.JSONDecodeError:
                        logger.warning(f"[{chunk_label}] JSON parse failed, trying regex extraction...")
                        match = re.search(r'\[\s*\{.*\}\s*\]', raw_output, re.DOTALL)
                        if match:
                            try:
                                json_str = match.group(0)
                                if json_str.endswith(','): json_str = json_str[:-1] + ']'
                                if not json_str.endswith(']'): json_str += ']'
                                data = json.loads(json_str)
                            except:
                                break
                        else:
                            break

                    if not isinstance(data, list):
                        data = [data]

                    added = 0
                    for item in data:
                        if not isinstance(item, dict): continue
                        obj = _coerce_criterion(item)
                        if obj is not None and obj.id not in seen_codes:
                            chunk_criteria.append(obj)
                            seen_codes.add(obj.id)
                            added += 1

                    logger.info(f"[{chunk_label}] ({model}): extracted {added} criteria.")
                    # Success path
                    return chunk_criteria

                except RateLimitError:
                    logger.warning(f"[{chunk_label}] {model} rate limited.")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                    else:
                        break # Try next model
                except Exception as e:
                    all_rate_limited = False # It was a different error
                    logger.error(f"[{chunk_label}] Error with {model}: {e}")
                    break

        if all_rate_limited:
            raise Exception("All Groq models are currently rate-limited. Please try again in a few minutes.")
        
        return chunk_criteria

    if len(tender_text) <= SINGLE_CALL_LIMIT:
        all_criteria = _call_llm(tender_text, "FULL")
    else:
        # Use smaller chunks to respect TPM
        chunk_size = 12_000 
        chunks = [tender_text[i:i + chunk_size] for i in range(0, len(tender_text), chunk_size)]
        logger.info(f"Splitting into {len(chunks)} chunks of {chunk_size} chars.")
        for i, chunk in enumerate(chunks):
            if i > 0: time.sleep(5)
            all_criteria.extend(_call_llm(chunk, f"CHUNK {i+1}/{len(chunks)}"))

    logger.info(f"Total criteria extracted: {len(all_criteria)}")
    return all_criteria
