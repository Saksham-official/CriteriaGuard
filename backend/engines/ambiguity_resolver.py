import json
import os

from groq import Groq

from utils.logger import logger

client = None
if os.getenv("GROQ_API_KEY"):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client in ambiguity resolver: {e}")

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
    is_mock = (
        os.getenv("MOCK_LLM", "").lower() in ("true", "1")
        or not os.getenv("GROQ_API_KEY")
        or client is None
    )

    if is_mock:
        # Check deontic markers
        lower_text = (criterion_text + " " + source_clause).lower()
        is_shall_must = "shall" in lower_text or "must" in lower_text or "required" in lower_text
        return {
            "likely_mandatory": is_shall_must,
            "confidence": "high" if is_shall_must else "medium",
            "reasoning": (
                "Clause employs imperative legal terminology ('shall'/'must') indicating binding obligation."
                if is_shall_must
                else "Clause uses advisory language ('should'/'preferred'). Suggesting officer review before disqualification."
            ),
            "recommendation": (
                "recommend confirming as mandatory"
                if is_shall_must
                else "recommend confirming as optional"
            ),
        }

    prompt = USER_PROMPT_TEMPLATE.format(
        criterion_text=criterion_text, surrounding_clause=source_clause
    )

    try:
        assert client is not None
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw_output = response.choices[0].message.content
        if not raw_output:
            raise ValueError("Model returned empty content")

        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0]

        return json.loads(raw_output.strip())
    except Exception as e:
        logger.error(f"Ambiguity resolution failed: {e}", exc_info=True)
        return {
            "likely_mandatory": True,
            "confidence": "low",
            "reasoning": "Could not analyze clause due to system error.",
            "recommendation": "recommend confirming as mandatory (fail-safe)",
        }
