# app/agent/groq_client.py
import os
import time
import json
import re

try:
    from groq import Groq
except Exception:
    Groq = None

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

# Create client if SDK available and key present
client = None
if Groq and GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)


PROMPT_TEMPLATE = """
You are a strict parser. Convert the admin's natural-language scheduling rule into a JSON object
with exactly two keys: "condition" and "action".

- condition: an object with field(s) to match (examples: patient_type: "new"/"returning", insurance_company: "BlueCross", age_gt: 65, dob: "YYYY-MM-DD", last_name: "Smith").
- action: an object with the intended scheduling action, possible keys:
    - assign_doctor: "<Doctor Name>"
    - duration: <minutes> (integer)
    - block_doctor: "<Doctor Name>"
    - prefer_doctor: "<Doctor Name>"
    - restrict_to_insurance: "<insurance name>"
    - any other simple key/value pairs as needed

Return valid JSON ONLY (no explanation). If a value is numeric, return a number. If uncertain, make best effort.

Example:
Input: "New patients should always be booked for 60 minutes."
Output JSON:
{"condition": {"patient_type": "new"}, "action": {"duration": 60}}

Now convert this rule:
<<RULE_TEXT>>
JSON:
"""

def _extract_json_from_text(text: str) -> str:
    """Try to extract JSON substring from LLM output."""
    # find first { and last } pair
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return text.strip()

def parse_rule_to_json(natural_rule: str, max_retries: int = 3, backoff: float = 1.0):
    """
    Send natural_rule to LLM and return a dict. Returns None on failure.
    """
    if not client:
        # No Groq client available — return None so caller can fallback
        return None, f"Groq client not configured (GROQ_API_KEY missing or SDK not installed)."

    prompt = PROMPT_TEMPLATE.replace("<<RULE_TEXT>>", natural_rule.strip())

    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=512
            )
            # Groq output access pattern may differ; adapt if needed
            content = None
            if hasattr(resp, "choices") and len(resp.choices) > 0:
                # Common pattern
                content = resp.choices[0].message.content
            else:
                # fallback to str(resp)
                content = str(resp)

            json_text = _extract_json_from_text(content)
            parsed = json.loads(json_text)
            return parsed, None
        except Exception as e:
            last_err = str(e)
            time.sleep(backoff * (attempt + 1))
            continue

    return None, f"Failed to parse rule after {max_retries} attempts: {last_err}"
