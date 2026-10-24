
import json


def detect_overflowing_elements(page):
    """
    Find visible HTML elements extending beyond
    the browser viewport's right edge.
    """

    return page.evaluate(
        """
        () => {
            const viewportWidth = window.innerWidth;
            const results = [];

            const elements = document.querySelectorAll("body *");

            for (const element of elements) {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();

                if (
                    style.display === "none" ||
                    style.visibility === "hidden" ||
                    rect.width === 0 ||
                    rect.height === 0
                ) {
                    continue;
                }

                if (rect.right <= viewportWidth + 1) {
                    continue;
                }

                let selector = element.tagName.toLowerCase();

                if (element.id) {
                    selector = "#" + CSS.escape(element.id);
                } else if (element.classList.length > 0) {
                    selector += "." + Array.from(
                        element.classList
                    ).map(name => CSS.escape(name)).join(".");
                }

                results.push({
                    selector: selector,
                    tag: element.tagName.toLowerCase(),
                    width: Math.round(rect.width),
                    right_edge: Math.round(rect.right),
                    viewport_width: viewportWidth
                });
            }

            return results;
        }
        """
    )


def select_repair_target(findings):
    """
    Select a likely repair target from overflowing elements.
    This is an initial heuristic, not guaranteed root-cause analysis.
    """

    if not findings:
        return None

    candidates = [
        finding
        for finding in findings
        if finding["selector"].startswith((".", "#", "div."))
    ]

    if candidates:
        return max(
            candidates,
            key=lambda item: item["right_edge"]
        )

    return None

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    url = "http://127.0.0.1:8765/mobile_overflow.html"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page(
                viewport={"width": 390, "height": 844}
            )

            page.goto(url, wait_until="load")

            findings = detect_overflowing_elements(page)
            target = select_repair_target(findings)
            print(json.dumps(findings, indent=2))
            print("\nSelected repair target:")
            print(json.dumps(target, indent=2))
        finally:
            browser.close()
