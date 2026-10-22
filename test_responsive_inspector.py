
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from inspector import inspect_page


VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 768},
}


def main():
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            for device_name, viewport in VIEWPORTS.items():
                page = browser.new_page(viewport=viewport)

                page.set_content("""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>OmniSight Responsive Test</title>
                    </head>
                    <body>
                        <div style="
                            width: 600px;
                            height: 100px;
                            background: tomato;
                        ">
                            Responsive layout test
                        </div>

                        <img src="missing-image.png">
                    </body>
                    </html>
                """)

                report = inspect_page(page)
                screenshot_dir = Path("screenshots")
                screenshot_dir.mkdir(exist_ok=True)

                screenshot_path = screenshot_dir / f"{device_name}_screenshot.png"
                page.screenshot(path=str(screenshot_path), full_page=True)

                print(f"Screenshot saved to: {screenshot_path}")
                
                report["device"] = device_name
                report["viewport_height"] = viewport["height"]

                report_path = report_dir / f"{device_name}_report.json"
                report_path.write_text(
                    json.dumps(report, indent=4),
                    encoding="utf-8"
                )

                print(f"\n--- {device_name.upper()} REPORT ---")
                print(json.dumps(report, indent=4))
                print(f"Saved to: {report_path}")

                page.close()

        finally:
            browser.close()


if __name__ == "__main__":
    main()
