import os
import json
from groq import Groq
from utils.logger import logger

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a senior government procurement analyst. You specialize in interpreting 
ambiguous language in tender documents.
"""

USER_PROMPT_TEMPLATE = """
A procurement officer needs help interpreting this eligibility criterion:
"{criterion_text}"

SURROUNDING CONTEXT:
"{surrounding_clause}"

Provide a structured analysis in this JSON format:
{{
  "likely_mandatory": true | false,
  "confidence": "low" | "medium" | "high",
  "reasoning": "2-3 sentence explanation citing specific language",
  "recommendation": "recommend confirming as mandatory | recommend confirming as optional"
}}
"""

def resolve_ambiguity(criterion_text: str, source_clause: str) -> dict:
    prompt = USER_PROMPT_TEMPLATE.format(
        criterion_text=criterion_text,
        surrounding_clause=source_clause
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        raw_output = response.choices[0].message.content
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0]
        
        return json.loads(raw_output.strip())
    except Exception as e:
        logger.error(f"Ambiguity resolution failed: {e}", exc_info=True)
        return {
            "likely_mandatory": True,
            "confidence": "low",
            "reasoning": "Could not analyze clause due to system error.",
            "recommendation": "recommend confirming as mandatory (fail-safe)"
        }
