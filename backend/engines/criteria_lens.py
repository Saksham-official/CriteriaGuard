import os
import json
from pydantic import ValidationError
from typing import List
from groq import Groq
from models.criterion import CriterionSchema
from prompts.criteria_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, RETRY_PROMPT_TEMPLATE
from utils.logger import logger

# Ensure groq client is initialized
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_criteria_from_text(tender_text: str) -> List[CriterionSchema]:
    # Chunking strategy to avoid Groq's 413 (Request too large) error.
    # Llama-3.3-70b-versatile has a limit of ~12k tokens on the free tier.
    # We use ~6000 tokens (approx 24000 characters) per chunk to be safe.
    import time
    from groq import RateLimitError

    # Reduced chunk size to manage token consumption better
    chunk_size = 16000 
    chunks = [tender_text[i:i + chunk_size] for i in range(0, len(tender_text), chunk_size)]
    
    all_criteria = []
    seen_codes = set()

    for i, chunk in enumerate(chunks):
        logger.info(f"Processing tender chunk {i+1}/{len(chunks)}...")
        user_prompt = USER_PROMPT_TEMPLATE.format(tender_text=chunk)
        
        max_retries = 3
        retry_delay = 5
        models_to_try = ["llama-3.3-70b-versatile", "llama3-8b-8192"]
        
        chunk_processed = False
        for model in models_to_try:
            if chunk_processed: break
            
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=4000,
                        temperature=0,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    
                    content = response.choices[0].message.content
                    raw_output = content.strip() if content else ""
                    
                    # Robust JSON cleaning
                    if "```json" in raw_output:
                        raw_output = raw_output.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_output:
                        raw_output = raw_output.split("```")[1].split("```")[0].strip()
                    
                    if not raw_output:
                        chunk_processed = True
                        break
                        
                    try:
                        data = json.loads(raw_output)
                    except json.JSONDecodeError:
                        import re
                        match = re.search(r'\[.*\]', raw_output, re.DOTALL)
                        if match:
                            data = json.loads(match.group(0))
                        else:
                            logger.error(f"Failed to parse JSON from chunk {i+1} using {model}.")
                            chunk_processed = True # Move to next chunk if parsing is hopeless
                            break
                    
                    if not isinstance(data, list):
                        data = [data]
                        
                    for item in data:
                        try:
                            obj = CriterionSchema(**item)
                            if obj.id not in seen_codes:
                                all_criteria.append(obj)
                                seen_codes.add(obj.id)
                        except ValidationError as ve:
                            logger.warning(f"Skipping invalid criterion in chunk {i+1}: {ve.json()}")
                            continue
                    
                    chunk_processed = True
                    break # Success!

                except RateLimitError as re:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit on {model} (Attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2 # Exponential backoff
                    else:
                        logger.error(f"Rate limit reached for {model} after {max_retries} attempts.")
                        # Will fall through to next model or next chunk
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1} with {model}: {e}")
                    chunk_processed = True # Stop retrying this chunk if it's a non-rate-limit error
                    break

    return all_criteria
