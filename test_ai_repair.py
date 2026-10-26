
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from inspector import inspect_page
from element_detector import (
    detect_overflowing_elements,
    select_repair_target,
)
from ai_repair_generator import generate_ai_css_fix


TEST_URL = "http://127.0.0.1:8765/mobile_overflow.html"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "small_mobile": {"width": 320, "height": 700},
    "desktop": {"width": 1366, "height": 768},
}


def has_horizontal_overflow(report):
    return report["browser_evidence"]["horizontal_overflow"]["detected"]


def test_ai_repair():
    evidence_dir = Path("screenshots/ai_repair")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            # Detect the issue on the normal mobile viewport
            page = browser.new_page(
                viewport=VIEWPORTS["mobile"]
            )

            try:
                page.goto(
                    TEST_URL,
                    wait_until="load",
                    timeout=30000,
                )

                before_report = inspect_page(page)

                issue = next(
                    (
                        item
                        for item in before_report["issues"]
                        if item["type"] == "horizontal_overflow"
                    ),
                    None,
                )

                if issue is None:
                    print("No horizontal overflow detected.")
                    return

                elements = detect_overflowing_elements(page)
                target = select_repair_target(elements)

            finally:
                page.close()

            # Ask Ollama to generate a repair
            print("Generating CSS repair using Ollama...")

            candidate = generate_ai_css_fix(issue, target)

            if candidate["status"] != "candidate_generated":
                print(json.dumps(candidate, indent=2))
                return

            print("\nAI-generated CSS:")
            print(candidate["css_fix"])

            # Validate the same CSS across three viewports
            for device, viewport in VIEWPORTS.items():
                page = browser.new_page(viewport=viewport)

                try:
                    page.goto(
                        TEST_URL,
                        wait_until="load",
                        timeout=30000,
                    )

                    page.screenshot(
                        path=str(
                            evidence_dir / f"{device}_before.png"
                        ),
                        full_page=True,
                    )

                    before = inspect_page(page)

                    # Apply AI CSS temporarily
                    page.add_style_tag(
                        content=candidate["css_fix"]
                    )

                    page.screenshot(
                        path=str(
                            evidence_dir / f"{device}_after.png"
                        ),
                        full_page=True,
                    )

                    after = inspect_page(page)

                    before_overflow = has_horizontal_overflow(before)
                    after_overflow = has_horizontal_overflow(after)

                    passed = not after_overflow

                    results[device] = {
                        "viewport_width": viewport["width"],
                        "before_overflow": before_overflow,
                        "after_overflow": after_overflow,
                        "passed": passed,
                    }

                finally:
                    page.close()

        finally:
            browser.close()

    overall_passed = (
        len(results) == len(VIEWPORTS)
        and all(
            result["passed"]
            for result in results.values()
        )
    )

    output = {
        "test": "OmniSight AI CSS Repair Validation",
        "ai_model": "qwen2.5vl:3b",
        "repair_target": candidate["selector"],
        "css_fix": candidate["css_fix"],
        "results": results,
        "overall_passed": overall_passed,
    }

    print("\nValidation results:")
    print(json.dumps(output, indent=2))

    if not overall_passed:
        print(
            "\nAI repair rejected: overflow remains "
            "on at least one viewport."
        )
    else:
        print(
            "\nAI repair passed overflow checks "
            "on all tested viewports."
        )


if __name__ == "__main__":
    test_ai_repair()
