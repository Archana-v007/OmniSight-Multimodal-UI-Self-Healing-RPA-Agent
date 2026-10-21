
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from inspector import inspect_page


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            page = browser.new_page(
                viewport={"width": 390, "height": 844}
            )

            # Create a test webpage with an intentional UI defect
            page.set_content("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title></title>
                </head>
                <body>
                    <div style="
                        width: 600px;
                        height: 100px;
                        background: tomato;
                    ">
                        This box is too wide for mobile!
                    </div>
                    <img src="missing-image.png">
                </body>
                </html>
            """)

            # Run the inspection engine
            report = inspect_page(page)

            # Create the reports folder if it doesn't exist
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)

            # Save the inspection results as JSON
            report_path = report_dir / "ui_report.json"
            report_path.write_text(
                json.dumps(report, indent=4),
                encoding="utf-8"
            )

            # Display the results
            print("Inspection results:")
            print(json.dumps(report, indent=4))
            print(f"JSON report saved to: {report_path}")

        finally:
            # Always close the browser
            browser.close()


if __name__ == "__main__":
    main()
