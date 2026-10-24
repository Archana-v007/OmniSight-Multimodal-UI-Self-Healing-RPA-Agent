
import json

from playwright.sync_api import sync_playwright

from inspector import inspect_page
from element_detector import (
    detect_overflowing_elements,
    select_repair_target,
)
from self_healer import generate_css_fix


TEST_URL = "http://127.0.0.1:8765/mobile_overflow.html"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 768},
}


def has_horizontal_overflow(report):
    return report["browser_evidence"]["horizontal_overflow"]["detected"]


def test_repair():
    results = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            for device, viewport in VIEWPORTS.items():
                page = browser.new_page(viewport=viewport)

                try:
                    page.goto(
                        TEST_URL,
                        wait_until="load",
                        timeout=30000,
                    )

                    before = inspect_page(page)

                    overflow_issue = next(
                        (
                            issue
                            for issue in before["issues"]
                            if issue["type"] == "horizontal_overflow"
                        ),
                        None,
                    )

                    target = None
                    candidate = {"status": "no_repair_needed"}

                    if overflow_issue:
                        elements = detect_overflowing_elements(page)
                        target = select_repair_target(elements)

                        candidate = generate_css_fix(
                            overflow_issue,
                            target,
                        )

                    if candidate["status"] == "candidate_generated":
                        page.add_style_tag(
                            content=candidate["css_fix"]
                        )

                    after = inspect_page(page)

                    before_overflow = has_horizontal_overflow(before)
                    after_overflow = has_horizontal_overflow(after)

                    repair_passed = (
                        not after_overflow
                        and (
                            not before_overflow
                            or candidate["status"]
                            == "candidate_generated"
                        )
                    )

                    results[device] = {
                        "before_overflow": before_overflow,
                        "after_overflow": after_overflow,
                        "selected_target": (
                            target["selector"] if target else None
                        ),
                        "repair_status": candidate["status"],
                        "passed": repair_passed,
                    }

                finally:
                    page.close()

        finally:
            browser.close()

    mobile = results["mobile"]
    desktop = results["desktop"]

    overall_passed = (
        mobile["before_overflow"]
        and mobile["selected_target"] == "div.container"
        and mobile["repair_status"] == "candidate_generated"
        and not mobile["after_overflow"]
        and not desktop["before_overflow"]
        and not desktop["after_overflow"]
    )

    print(
        json.dumps(
            {
                "test": "OmniSight Dynamic CSS Self-Healing",
                "results": results,
                "overall_passed": overall_passed,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    test_repair()
