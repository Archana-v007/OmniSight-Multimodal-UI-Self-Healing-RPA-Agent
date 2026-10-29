
from ai_repair_retry import generate_with_retries
import ai_repair_retry


def fake_generate_ai_css_fix(issue, target, feedback=None):
    """Simulate AI output without calling Ollama."""
    if feedback is None:
        return {
            "status": "candidate_generated",
            "css_fix": ".container { width: 600px; }",
        }

    return {
        "status": "candidate_generated",
        "css_fix": (
            "@media (max-width: 767px) { "
            ".container { max-width: 100%; box-sizing: border-box; } "
            "}"
        ),
    }


def fake_validator(css_fix):
    """Simulate the first candidate failing and the second passing."""
    passed = "max-width: 100%" in css_fix

    return {
        "overall_passed": passed,
        "results": {
            "mobile": {
                "passed": passed,
                "message": (
                    "No overflow detected."
                    if passed
                    else "Horizontal overflow remains."
                ),
            }
        },
    }


def main():
    # Replace the model call only for this isolated test.
    original_generator = ai_repair_retry.generate_ai_css_fix
    ai_repair_retry.generate_ai_css_fix = fake_generate_ai_css_fix

    try:
        result = generate_with_retries(
            issue={"type": "horizontal_overflow"},
            target={"selector": ".container"},
            validator=fake_validator,
            max_attempts=3,
        )
    finally:
        ai_repair_retry.generate_ai_css_fix = original_generator

    assert result["status"] == "repair_validated", result
    assert result["attempts"] == 2, result
    assert result["history"][0]["passed"] is False
    assert result["history"][1]["passed"] is True

    print("\nSUCCESS: retry logic passed.")
    print(f"Attempts used: {result['attempts']}")
    print("Attempt 1: failed as expected.")
    print("Attempt 2: passed as expected.")


if __name__ == "__main__":
    main()
