
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    # Desktop screen
    desktop = browser.new_page(
        viewport={"width": 1366, "height": 768}
    )
    desktop.goto("https://example.com")
    desktop.screenshot(path="desktop_screenshot.png")
    print("Desktop screenshot saved!")

    # Mobile screen
    mobile = browser.new_page(
        viewport={"width": 390, "height": 844},
        is_mobile=True
    )
    mobile.goto("https://example.com")
    mobile.screenshot(path="mobile_screenshot.png")
    print("Mobile screenshot saved!")

    browser.close()
