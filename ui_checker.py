
from pathlib import Path
from playwright.sync_api import sync_playwright

# Create the screenshots folder if it doesn't exist
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

with sync_playwright() as p:
    # Launch the browser
    browser = p.chromium.launch(headless=True)

    # Open a mobile-sized browser page
    page = browser.new_page(
        viewport={"width": 390, "height": 844}
    )

    # Load a sample page containing a mobile layout bug
    page.set_content("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OmniSight UI Bug Test</title>
        </head>
        <body>
            <div style="
                width: 600px;
                height: 100px;
                background: tomato;
            ">
                This box is too wide for a mobile screen!
            </div>
        </body>
        </html>
    """)

    # Capture the page screenshot
    screenshot_path = SCREENSHOT_DIR / "ui_bug.png"
    page.screenshot(
        path=str(screenshot_path),
        full_page=True
    )

    # Collect page information
    page_title = page.title()
    viewport_width = page.evaluate("window.innerWidth")
    page_width = page.locator("body").evaluate(
        "(element) => element.scrollWidth"
    )

    # Check whether the page title is missing
    if not page_title.strip():
        print("Possible UI issue: page title is missing!")
    else:
        print("Page title is present.")

    # Print page information
    print("Page title:", page_title)
    print("Viewport width:", viewport_width)
    print("Page content width:", page_width)
    print("Screenshot saved to:", screenshot_path)

    # Detect horizontal overflow
    if page_width > viewport_width:
        print("Possible UI issue: horizontal overflow detected!")
    else:
        print("No horizontal overflow detected.")

    # Close the browser after all checks are complete
    browser.close()
