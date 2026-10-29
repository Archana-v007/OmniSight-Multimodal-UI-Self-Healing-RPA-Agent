
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from inspector import inspect_page
from element_detector import (
    detect_overflowing_elements,
    select_repair_target,
)
from ai_repair_retry import generate_with_retries


TEST_URL = "http://127.0.0.1:8765/mobile_overflow.html"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "small_mobile": {"width": 320, "height": 700},
    "desktop": {"width": 1366, "height": 768},
}


def has_horizontal_overflow(report):
    return report["browser_evidence"]["horizontal_overflow"]["detected"]


def validate_css(browser, css_fix, attempt):
    results = {}
    evidence_dir = Path("screenshots/ai_repair_retry")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    for device, viewport in VIEWPORTS.items():
        page = browser.new_page(viewport=viewport)

        try:
            page.goto(TEST_URL, wait_until="load", timeout=30000)

            before_report = inspect_page(page)
            before_overflow = has_horizontal_overflow(before_report)

            page.screenshot(
                path=str(
                    evidence_dir
                    / f"attempt_{attempt}_{device}_before.png"
                ),
                full_page=True,
            )

            page.add_style_tag(content=css_fix)

            after_report = inspect_page(page)
            after_overflow = has_horizontal_overflow(after_report)

            page.screenshot(
                path=str(
                    evidence_dir
                    / f"attempt_{attempt}_{device}_after.png"
                ),
                full_page=True,
            )

            results[device] = {
                "viewport_width": viewport["width"],
                "before_overflow": before_overflow,
                "after_overflow": after_overflow,
                "passed": not after_overflow,
            }

        finally:
            page.close()

    return {
        "overall_passed": (
            len(results) == len(VIEWPORTS)
            and all(item["passed"] for item in results.values())
        ),
        "results": results,
    }


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page(viewport=VIEWPORTS["mobile"])

            try:
                page.goto(
                    TEST_URL,
                    wait_until="load",
                    timeout=30000,
                )

                report = inspect_page(page)

                issue = next(
                    (
                        item
                        for item in report["issues"]
                        if item["type"] == "horizontal_overflow"
                    ),
                    None,
                )

                if issue is None:
                    print("No horizontal overflow detected.")
                    return

                elements = detect_overflowing_elements(page)
                target = select_repair_target(elements)

                if not target:
                    print("No repair target identified.")
                    return

                print("Detected issue:", issue)
                print("Selected repair target:", target)

            finally:
                page.close()

            attempt_counter = {"value": 0}

            def validator(css_fix):
                attempt_counter["value"] += 1
                return validate_css(
                    browser,
                    css_fix,
                    attempt_counter["value"],
                )

            print("\nStarting automated AI repair loop...")

            result = generate_with_retries(
                issue=issue,
                target=target,
                validator=validator,
                max_attempts=3,
            )

            report_path = Path("reports/ai_repair_retry.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)

            report_path.write_text(
                json.dumps(result, indent=2),
                encoding="utf-8",
            )

            print("\nFinal retry result:")
            print(json.dumps(result, indent=2))
            print(f"\nReport saved to: {report_path}")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
