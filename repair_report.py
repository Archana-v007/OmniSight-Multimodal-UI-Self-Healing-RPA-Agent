
import json
from datetime import datetime, timezone
from pathlib import Path


def generate_repair_report(
    results,
    output_path="reports/repair_evidence.json"
):
    """
    Generate and save a structured self-healing evidence report.
    """

    mobile = results.get("mobile", {})
    desktop = results.get("desktop", {})

    overall_passed = (
        mobile.get("before_overflow") is True
        and mobile.get("after_overflow") is False
        and mobile.get("repair_status") == "candidate_generated"
        and mobile.get("passed") is True
        and desktop.get("before_overflow") is False
        and desktop.get("after_overflow") is False
        and desktop.get("passed") is True
    )

    report = {
        "project": "OmniSight",
        "report_type": "CSS Self-Healing Evidence",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_passed": overall_passed,
        "repair_target": mobile.get("selected_target"),
        "devices": {},
    }

    for device in ("mobile", "desktop"):
        device_result = results.get(device, {})

        report["devices"][device] = {
            "before_overflow": device_result.get(
                "before_overflow"
            ),
            "after_overflow": device_result.get(
                "after_overflow"
            ),
            "selected_target": device_result.get(
                "selected_target"
            ),
            "repair_status": device_result.get(
                "repair_status"
            ),
            "validation_passed": device_result.get(
                "passed"
            ),
            "screenshots": {
                "before": (
                    f"screenshots/self_healing/"
                    f"{device}_before.png"
                ),
                "after": (
                    f"screenshots/self_healing/"
                    f"{device}_after.png"
                ),
            },
        }

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    return report


if __name__ == "__main__":

    sample_results = {
        "mobile": {
            "before_overflow": True,
            "after_overflow": False,
            "selected_target": "div.container",
            "repair_status": "candidate_generated",
            "passed": True,
        },
        "desktop": {
            "before_overflow": False,
            "after_overflow": False,
            "selected_target": None,
            "repair_status": "no_repair_needed",
            "passed": True,
        },
    }

    report = generate_repair_report(
        sample_results
    )

    print(
        json.dumps(report, indent=2)
    )

    print(
        "\nReport saved to: "
        "reports/repair_evidence.json"
    )
