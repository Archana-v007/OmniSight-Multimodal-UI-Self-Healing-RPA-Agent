
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from inspector import inspect_page


VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 768},
}


def save_json_report(report, report_path):
    """Save one inspection report as formatted JSON."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )


def inspect_url(
    url,
    reports_dir=Path("reports"),
    screenshots_dir=Path("screenshots"),
    viewports=None,
    timeout_ms=15000,
):
    """Inspect a URL at multiple viewport sizes."""

    if viewports is None:
        viewports = VIEWPORTS

    reports_dir = Path(reports_dir)
    screenshots_dir = Path(screenshots_dir)

    reports_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            for device, viewport in viewports.items():
                page = None

                report = {
                    "url": url,
                    "device": device,
                    "viewport_width": viewport["width"],
                    "viewport_height": viewport["height"],
                    "status": "error",
                    "page_title": "",
                    "issues_found": 0,
                    "issues": [],
                    "screenshot_path": None,
                    "error": None,
                }

                try:
                    page = browser.new_page(viewport=viewport)

                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )

                    if response is not None:
                        report["http_status"] = response.status

                    report["page_title"] = page.title()

                    screenshot_path = (
                        screenshots_dir / f"{device}_screenshot.png"
                    )

                    page.screenshot(
                        path=str(screenshot_path),
                        full_page=True,
                    )

                    report["screenshot_path"] = str(screenshot_path)

                    findings = inspect_page(page)

                    report.update(findings)
                    report["url"] = url
                    report["device"] = device
                    report["viewport_height"] = viewport["height"]
                    report["status"] = "success"

                except Exception as exc:
                    report["error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )

                finally:
                    if page is not None:
                        page.close()

                report_path = reports_dir / f"{device}_report.json"
                save_json_report(report, report_path)

                report["report_path"] = str(report_path)
                results.append(report)

                print(f"\n--- {device.upper()} ---")
                print(f"Status: {report['status']}")
                print(f"Issues found: {report['issues_found']}")

                if report["error"]:
                    print(f"Error: {report['error']}")
                else:
                    print(
                        "Screenshot: "
                        f"{report['screenshot_path']}"
                    )

                print(f"Report: {report_path}")

        finally:
            browser.close()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="OmniSight responsive UI inspection runner"
    )

    parser.add_argument(
        "url",
        help="URL of the webpage to inspect",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=15000,
        help="Page navigation timeout in milliseconds",
    )

    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    inspect_url(
        url=args.url,
        timeout_ms=args.timeout,
    )


if __name__ == "__main__":
    main()
