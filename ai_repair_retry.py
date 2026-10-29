import json

from ai_repair_generator import generate_ai_css_fix


def generate_with_retries(issue, target, validator, max_attempts=3):
    """
    Generate and validate AI CSS repairs.

    validator(css_fix) must return a dictionary containing:
        overall_passed: bool
        results: dict
    """

    history = []
    feedback = None

    for attempt in range(1, max_attempts + 1):
        print(f"\nAI repair attempt {attempt}/{max_attempts}")

        candidate = generate_ai_css_fix(
            issue,
            target,
            feedback=feedback
        )

        if candidate["status"] != "candidate_generated":
            history.append({
                "attempt": attempt,
                "generation_status": candidate["status"],
                "message": candidate.get("message")
            })

            feedback = {
                "error": candidate.get("message", "Generation failed")
            }
            continue

        css_fix = candidate["css_fix"]

        print("\nGenerated CSS:")
        print(css_fix)

        validation = validator(css_fix)

        passed = validation.get("overall_passed", False)

        history.append({
            "attempt": attempt,
            "css_fix": css_fix,
            "validation": validation,
            "passed": passed
        })

        if passed:
            print("\nAI repair successfully validated!")

            return {
                "status": "repair_validated",
                "attempts": attempt,
                "css_fix": css_fix,
                "history": history
            }

        print("\nRepair failed. Sending feedback to Ollama...")

        feedback = {
            "previous_css": css_fix,
            "validation_results": validation.get("results", {}),
            "instruction": (
                "Fix the remaining overflow without "
                "breaking previously passing viewports."
            )
        }

    return {
        "status": "repair_failed",
        "attempts": max_attempts,
        "css_fix": None,
        "history": history
    }


if __name__ == "__main__":
    print(
        "AI retry engine created successfully. "
        "Connect it to Playwright validation next."
    )