import os
import json
from pydantic import ValidationError
from typing import List
from groq import Groq
from models.criterion import CriterionSchema
from prompts.criteria_extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, RETRY_PROMPT_TEMPLATE

# Ensure groq client is initialized
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_criteria_from_text(tender_text: str) -> List[CriterionSchema]:
    user_prompt = USER_PROMPT_TEMPLATE.format(tender_text=tender_text)
    
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
        
        # More robust JSON cleaning
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_output)
        
        # Validate with Pydantic
        return [CriterionSchema(**item) for item in data]
        
    except (ValidationError, json.JSONDecodeError) as e:
        # Implement retry logic
        print(f"Validation failed. Retrying... Error: {e}")
        retry_prompt = RETRY_PROMPT_TEMPLATE.format(
            validation_error=str(e),
            schema_json=CriterionSchema.model_json_schema()
        )
        
        retry_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
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
        return [CriterionSchema(**item) for item in retry_data]
