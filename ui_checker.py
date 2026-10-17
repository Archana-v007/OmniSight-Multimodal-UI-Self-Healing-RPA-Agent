
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        viewport={"width": 390, "height": 844}
    )

    page.set_content("""
        <title>OmniSight UI Bug Test</title>
        <div style="width: 600px; height: 100px; background: tomato;">
            This box is too wide for a mobile screen!
        </div>
    """)

    # Save a screenshot of the UI
    page.screenshot(path="ui_bug.png", full_page=True)

    # Collect page information
    page_title = page.title()
    viewport_width = page.evaluate("window.innerWidth")
    page_width = page.locator("body").evaluate(
        "(element) => element.scrollWidth"
    )

    print("Page title:", page_title)
    print("Viewport width:", viewport_width)
    print("Page content width:", page_width)

    if page_width > viewport_width:
        print("Possible UI issue: horizontal overflow detected!")
    else:
        print("No horizontal overflow detected.")

    browser.close()
