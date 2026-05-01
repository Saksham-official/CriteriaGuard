import os
import json
from pydantic import ValidationError
from typing import Dict, Any
from groq import Groq

from models.extraction import ExtractionSchema
from prompts.value_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, RETRY_PROMPT_TEMPLATE

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_value_for_criterion(criterion_dict: dict, documents_with_labels: str) -> ExtractionSchema:
    user_prompt = USER_PROMPT_TEMPLATE.format(
        criterion_json=json.dumps(criterion_dict, indent=2),
        documents_with_labels=documents_with_labels,
        criterion_id=criterion_dict.get('id', 'unknown')
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            max_tokens=2000,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        raw_output = response.choices[0].message.content
        
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3]
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:-3]
            
        data = json.loads(raw_output.strip())
        
        return ExtractionSchema(**data)
        
    except (ValidationError, json.JSONDecodeError) as e:
        print(f"DocProbe Validation failed. Retrying... Error: {e}")
        retry_prompt = RETRY_PROMPT_TEMPLATE.format(
            validation_error=str(e),
            schema_json=ExtractionSchema.model_json_schema()
        )
        
        retry_response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
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
        if retry_output.startswith("```json"):
            retry_output = retry_output[7:-3]
        elif retry_output.startswith("```"):
            retry_output = retry_output[3:-3]
            
        retry_data = json.loads(retry_output.strip())
        return ExtractionSchema(**retry_data)
