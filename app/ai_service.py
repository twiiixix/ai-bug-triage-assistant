import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def analyze_bug_with_ai(title: str, description: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "your_api_key_here":
        return None

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    prompt = f"""
Analyze this software bug report.

Title:
{title}

Description:
{description}

Return only valid JSON with this exact structure:
{{
  "summary": "brief summary",
  "severity": "Low, Medium, High, or Critical",
  "category": "short software category",
  "possible_causes": ["cause one", "cause two", "cause three"],
  "recommended_steps": ["step one", "step two", "step three"]
}}
"""

    try:
        response = client.responses.create(model=model, input=prompt)
        analysis = json.loads(response.output_text)

        required = {
            "summary",
            "severity",
            "category",
            "possible_causes",
            "recommended_steps",
        }

        if not required.issubset(analysis):
            return None

        return analysis
    except Exception as error:
        print(f"AI analysis failed; using fallback analysis: {error}")
        return None
