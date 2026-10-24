
import json


def generate_css_fix(issue, target=None):
    """
    Generate a candidate CSS fix for horizontal overflow.

    The target must come from browser element detection.
    This function does not modify the original webpage.
    """

    if issue.get("type") != "horizontal_overflow":
        return {
            "status": "unsupported",
            "reason": "No repair strategy exists for this issue type.",
        }

    viewport_width = issue.get("viewport_width")

    if (
        isinstance(viewport_width, bool)
        or not isinstance(viewport_width, int)
        or viewport_width <= 0
    ):
        return {
            "status": "error",
            "reason": "A valid viewport width is required.",
        }

    if not isinstance(target, dict):
        return {
            "status": "error",
            "reason": "A detected repair target is required.",
        }

    selector = target.get("selector")

    if (
        not isinstance(selector, str)
        or not selector.strip()
        or any(char in selector for char in "{};\n\r")
    ):
        return {
            "status": "error",
            "reason": "The repair target has an invalid CSS selector.",
        }

    css_fix = f"""
@media (max-width: 767px) {{
    {selector} {{
        box-sizing: border-box;
        max-width: 100%;
    }}
}}
""".strip()

    return {
        "status": "candidate_generated",
        "issue_type": "horizontal_overflow",
        "viewport_width": viewport_width,
        "target_selector": selector,
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

    test_target = {
        "selector": "div.container",
        "width": 640,
        "right_edge": 656,
        "viewport_width": 390,
    }

    result = generate_css_fix(test_issue, test_target)
    print(json.dumps(result, indent=2))
