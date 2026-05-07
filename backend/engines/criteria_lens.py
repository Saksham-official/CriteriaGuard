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
    chunk_size = 24000 
    chunks = [tender_text[i:i + chunk_size] for i in range(0, len(tender_text), chunk_size)]
    
    all_criteria = []
    seen_codes = set()

    for i, chunk in enumerate(chunks):
        logger.info(f"Processing tender chunk {i+1}/{len(chunks)}...")
        user_prompt = USER_PROMPT_TEMPLATE.format(tender_text=chunk)
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            raw_output = response.choices[0].message.content.strip()
            
            # Robust JSON cleaning
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
            if not raw_output:
                continue
                
            data = json.loads(raw_output)
            
            for item in data:
                try:
                    obj = CriterionSchema(**item)
                    # Deduplicate if the same criterion appears in overlapping or multiple chunks
                    if obj.id not in seen_codes:
                        all_criteria.append(obj)
                        seen_codes.add(obj.id)
                except ValidationError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing chunk {i+1}: {e}", exc_info=True)
            # If one chunk fails, we continue to others to extract as much as possible
            continue

    return all_criteria
