import os
import json
from pydantic import ValidationError
from typing import Dict, Any
from groq import Groq

from models.extraction import ExtractionSchema
from prompts.value_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, RETRY_PROMPT_TEMPLATE
from utils.logger import logger

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_value_for_criterion(criterion_dict: dict, documents_with_labels: str) -> ExtractionSchema:
    # Safety truncation for Groq free tier (approx 25k chars ~ 6k tokens)
    documents_with_labels = documents_with_labels[:25000]

    user_prompt = USER_PROMPT_TEMPLATE.format(
        criterion_json=json.dumps(criterion_dict, indent=2),
        documents_with_labels=documents_with_labels,
        criterion_id=criterion_dict.get('id', 'unknown')
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # More robust JSON cleaning
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_output)
        
        return ExtractionSchema(**data)
        
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"DocProbe Validation failed. Retrying... Error: {e}", exc_info=True)
        retry_prompt = RETRY_PROMPT_TEMPLATE.format(
            validation_error=str(e),
            schema_json=ExtractionSchema.model_json_schema()
        )
        
        retry_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": raw_output if 'raw_output' in locals() else "{}"},
                {"role": "user", "content": retry_prompt}
            ]
        )
        
        retry_output = retry_response.choices[0].message.content.strip()
        if "```json" in retry_output:
            retry_output = retry_output.split("```json")[1].split("```")[0].strip()
        elif "```" in retry_output:
            retry_output = retry_output.split("```")[1].split("```")[0].strip()
            
        retry_data = json.loads(retry_output)
        return ExtractionSchema(**retry_data)
