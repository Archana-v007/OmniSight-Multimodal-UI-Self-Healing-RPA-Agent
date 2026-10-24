
import json


def generate_css_fix(issue):
    """
    Generate a candidate CSS fix for a verified UI issue.
    This function does not modify the original website.
    """

    if issue.get("type") != "horizontal_overflow":
        return {
            "status": "unsupported",
            "reason": "No repair strategy exists for this issue type.",
        }

    viewport_width = issue.get("viewport_width")

    if not isinstance(viewport_width, int) or viewport_width <= 0:
        return {
            "status": "error",
            "reason": "A valid viewport width is required.",
        }

    css_fix = """
@media (max-width: 767px) {
    .container {
        box-sizing: border-box;
        max-width: 100%;
    }
}
""".strip()

    return {
        "status": "candidate_generated",
        "issue_type": "horizontal_overflow",
        "viewport_width": viewport_width,
        "target_selector": ".container",
        "css_fix": css_fix,
        "requires_validation": True,
    }


if __name__ == "__main__":
    test_issue = {
        "type": "horizontal_overflow",
        "severity": "high",
        "viewport_width": 390,
        "page_width": 640,
    }

    result = generate_css_fix(test_issue)
    print(json.dumps(result, indent=2))
