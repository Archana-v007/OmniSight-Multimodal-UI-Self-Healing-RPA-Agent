
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


MODEL = "qwen2.5vl:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"


def analyze_screenshot(image_path, viewport_width=390):
    """Ask a local vision model to inspect a webpage screenshot."""
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {image_path}"
        )

    image_data = base64.b64encode(
        image_path.read_bytes()
    ).decode("utf-8")

    prompt = f"""
You are OmniSight, a careful UI testing assistant.

Analyze the supplied webpage screenshot at a viewport width
of {viewport_width} pixels.

Return valid JSON only, using this structure:
{{
  "visual_issue_detected": true,
  "issue_type": "horizontal_overflow",
  "evidence": "Describe only what is visible in the image.",
  "likely_cause": "State a possible cause, not a certainty.",
  "suggested_fix": "Give a targeted CSS suggestion.",
  "confidence": 0.0
}}

Rules:
- Set visual_issue_detected to true only when there is visible evidence.
- Do not claim to see content that is not visible.
- For mobile layouts, make suggestions suitable for a
  {viewport_width}-pixel viewport.
- Do not assume max-width: 1000px fixes mobile overflow.
- If the screenshot is insufficient to confirm overflow,
  say so in the evidence and lower your confidence.
- Use a confidence value between 0 and 1.
- Return JSON only, without Markdown fences.
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [image_data],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0}
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=300
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not reach Ollama. Make sure Ollama is running."
        ) from exc

    try:
        analysis = json.loads(result["response"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "The model did not return valid JSON."
        ) from exc

    required_fields = {
        "visual_issue_detected",
        "issue_type",
        "evidence",
        "likely_cause",
        "suggested_fix",
        "confidence",
    }

    if not required_fields.issubset(analysis):
        raise RuntimeError(
            "The model response is missing required fields."
        )

    confidence = analysis["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        raise RuntimeError(
            "The model returned an invalid confidence value."
        )

    return {
        "model": MODEL,
        "screenshot_path": str(image_path),
        "viewport_width": viewport_width,
        "analysis": analysis,
    }


def main():
    image_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("screenshots/mobile_screenshot.png")
    )

    report_path = Path("reports/ai_mobile_analysis.json")

    try:
        report = analyze_screenshot(image_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"AI analysis failed: {exc}")
        raise SystemExit(1)

    print(json.dumps(report, indent=2))
    print(f"\nAI report saved to: {report_path}")


if __name__ == "__main__":
    main()
