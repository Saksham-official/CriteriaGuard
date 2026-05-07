import os
import json
from pydantic import ValidationError
from typing import Dict, Any
from groq import Groq

from models.extraction import ExtractionSchema
from prompts.value_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, RETRY_PROMPT_TEMPLATE
from utils.logger import logger

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Live Groq models as of May 2026
MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct", 
    "llama-3.3-70b-versatile",                   
    "qwen/qwen3-32b",                            
    "llama-3.1-8b-instant",                      
]

def extract_value_for_criterion(criterion_dict: dict, documents_with_labels: str) -> ExtractionSchema:
    import httpx
    import re
    from groq import RateLimitError
    import time

    # Safety truncation for Groq free tier
    documents_with_labels = documents_with_labels[:25000]

    user_prompt = USER_PROMPT_TEMPLATE.format(
        criterion_json=json.dumps(criterion_dict, indent=2),
        documents_with_labels=documents_with_labels,
        criterion_id=criterion_dict.get('id', 'unknown')
    )
    
    for model in MODELS:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"DocProbe: Calling {model} for criterion {criterion_dict.get('id', '?')} (attempt {attempt+1})")
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=3000,  # Increased from 2000
                    temperature=0,
                    timeout=httpx.Timeout(60.0, connect=10.0),
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                content = response.choices[0].message.content
                raw_output = content.strip() if content else ""
                
                if not raw_output:
                    continue

                # Strip markdown code fences
                if "```json" in raw_output:
                    raw_output = raw_output.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_output:
                    raw_output = raw_output.split("```")[1].split("```")[0].strip()
                    
                try:
                    data = json.loads(raw_output)
                except json.JSONDecodeError:
                    # Regex fallback
                    match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(0))
                        except:
                            continue
                    else:
                        continue

                # Basic validation: ensure it's a dict
                if not isinstance(data, dict):
                    continue
                
                # Ensure criterion_id matches (LLM sometimes hallucinates it)
                data["criterion_id"] = str(criterion_dict.get("id"))

                return ExtractionSchema(**data)
                
            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    break # Try next model
            except Exception as e:
                logger.warning(f"DocProbe: Model {model} failed with {type(e).__name__}: {e}")
                break # Try next model

    # Fallback: return a "not found" extraction if all models fail
    return ExtractionSchema(
        criterion_id=str(criterion_dict.get("id")),
        value_found=False,
        not_found_reason="value_unreadable",
        ocr_quality="low",
        alignment_score=0,
        authenticity_score=0,
        notes="All LLM extraction attempts failed (potential rate limit or model timeout)."
    )
