
import json
import re

import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5vl:3b"


def generate_ai_css_fix(issue, target, feedback=None):
    """
    Ask local Ollama to suggest a CSS fix for a detected UI issue.
    This function does not modify any source files.
    """

    if not target or not target.get("selector"):
        return {
            "status": "no_target",
            "css_fix": None,
            "message": "No valid repair target was provided.",
        }

    selector = target["selector"]

    prompt = f"""
You are a frontend CSS debugging assistant.

A Playwright browser inspection found this UI problem:

{json.dumps(issue, indent=2)}

The overflowing element is:

{json.dumps(target, indent=2)}

Generate a minimal CSS fix for the element with selector:
{selector}

Requirements:
- Fix horizontal overflow on mobile screens, including 320px and 390px widths.
- Avoid changing the desktop layout.
- Account for padding and borders when calculating element width.
- Prefer responsive percentage-based sizing instead of fixed pixel widths.
- The target element has padding that contributes to horizontal overflow.
- You MUST include box-sizing: border-box in the generated CSS rule.
- You MUST include max-width: 100% in the generated CSS rule.
- Do not use fixed pixel widths for the repaired element.
- Preserve the original desktop layout.
- Ensure the element fits inside its containing block.
- Do not hardcode viewport-specific widths such as 320px or 390px.
- Use a media query with max-width: 767px.
- Use only standard CSS properties.
- Do not use JavaScript.
- Do not modify HTML.
- Do not use !important.
- Do not hide content using display:none or visibility:hidden.
- Do not use overflow:hidden to conceal the problem.

Return ONLY a JSON object in this format:

{{
  "selector": "{selector}",
  "css_fix": "@media (max-width: 767px) {{ ... }}",
  "explanation": "Brief explanation"
}}
"""

    if feedback:
        prompt += f"""

PREVIOUS REPAIR FAILED VALIDATION.

Browser validation feedback:
{json.dumps(feedback, indent=2)}

Generate a corrected CSS repair.

Requirements:
- Address every failed viewport.
- Correct the underlying layout problem.
- Do not repeat the previously failed CSS.
- Preserve desktop layout.
- Return only the requested JSON object.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                    "num_predict": 350,
                },
            },
            timeout=180,
        )

        response.raise_for_status()

        raw_response = response.json().get("response", "")
        data = json.loads(raw_response)

        css_fix = data.get("css_fix")
        returned_selector = data.get("selector")

        if not isinstance(css_fix, str) or not css_fix.strip():
            raise ValueError("AI returned an empty CSS fix.")

        if returned_selector != selector:
            raise ValueError("AI changed the selected CSS target.")

        if not re.search(r"@media\s*\(", css_fix):
            raise ValueError("AI fix does not contain a media query.")

        return {
            "status": "candidate_generated",
            "selector": selector,
            "css_fix": css_fix,
            "explanation": data.get("explanation", ""),
            "source": "ollama",
        }

    except (requests.RequestException, ValueError, KeyError) as error:
        return {
            "status": "generation_failed",
            "selector": selector,
            "css_fix": None,
            "message": str(error),
        }


if __name__ == "__main__":
    sample_issue = {
        "type": "horizontal_overflow",
        "severity": "high",
        "viewport_width": 390,
        "page_width": 640,
    }

    sample_target = {
        "selector": "div.container",
        "width": 640,
        "right_edge": 656,
        "viewport_width": 390,
    }

    print("Asking local Ollama to generate a CSS repair...")

    result = generate_ai_css_fix(
        sample_issue,
        sample_target,
    )

    print(json.dumps(result, indent=2))
