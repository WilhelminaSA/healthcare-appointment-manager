import json
import requests


# --------------------------------------------------
# Ollama Configuration
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


# --------------------------------------------------
# Generate Pre-Visit AI Summary
# --------------------------------------------------

def generate_pre_visit_summary(symptoms):
    """
    Generate a structured pre-visit summary from
    patient-provided symptoms using a local Ollama LLM.

    Returns:
        dict containing:
        - urgency_level
        - chief_complaint
        - suggested_question_1
        - suggested_question_2
        - suggested_question_3
    """

    prompt = f"""
Analyse the following patient symptoms and generate a concise
pre-visit summary for a doctor.

Return ONLY valid JSON with exactly these fields:

{{
    "urgency_level": "Low",
    "chief_complaint": "",
    "suggested_question_1": "",
    "suggested_question_2": "",
    "suggested_question_3": ""
}}

Rules:

1. urgency_level MUST be exactly one of:
   Low, Medium, High

2. chief_complaint must be a concise description
   of the patient's main complaint.

3. Provide exactly three suggested questions
   that the doctor should consider asking.

4. Do not provide a diagnosis.

5. Do not provide treatment recommendations.

6. Do not provide medical advice.

7. Return JSON only.

Patient symptoms:
{symptoms}
"""

    # --------------------------------------------------
    # Call Ollama
    # --------------------------------------------------

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a clinical pre-visit "
                        "summarization assistant. "
                        "You summarize patient-provided "
                        "symptoms for a doctor. "
                        "You do not diagnose, prescribe, "
                        "or provide treatment recommendations. "
                        "You must return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    # --------------------------------------------------
    # Check Ollama response
    # --------------------------------------------------

    response.raise_for_status()

    response_data = response.json()

    # Ollama returns the model's message here
    content = response_data["message"]["content"]

    # --------------------------------------------------
    # Convert JSON string → Python dictionary
    # --------------------------------------------------

    result = json.loads(content)

    # --------------------------------------------------
    # Validate required fields
    # --------------------------------------------------

    required_fields = [
        "urgency_level",
        "chief_complaint",
        "suggested_question_1",
        "suggested_question_2",
        "suggested_question_3"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"AI response missing required field: {field}"
            )

    # --------------------------------------------------
    # Validate urgency level
    # --------------------------------------------------

    if result["urgency_level"] not in [
        "Low",
        "Medium",
        "High"
    ]:
        raise ValueError(
            "Invalid urgency level returned by AI"
        )

    # --------------------------------------------------
    # Return structured result
    # --------------------------------------------------

    return {
        "urgency_level": result["urgency_level"],
        "chief_complaint": result["chief_complaint"],
        "suggested_question_1": result[
            "suggested_question_1"
        ],
        "suggested_question_2": result[
            "suggested_question_2"
        ],
        "suggested_question_3": result[
            "suggested_question_3"
        ]
    }

