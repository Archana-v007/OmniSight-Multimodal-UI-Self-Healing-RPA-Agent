
def check_page_title(page):
    """Check whether the webpage has a meaningful title."""

    title = page.title()

    if not title.strip():
        return {
            "type": "missing_page_title",
            "severity": "medium",
            "message": "The webpage has no title."
        }

    return None


def check_horizontal_overflow(page):
    """Check whether page content exceeds the viewport width."""

    viewport_width = page.evaluate("window.innerWidth")
    page_width = page.locator("body").evaluate(
        "(element) => element.scrollWidth"
    )

    if page_width > viewport_width:
        return {
            "type": "horizontal_overflow",
            "severity": "high",
            "message": "Page content exceeds the viewport width.",
            "viewport_width": viewport_width,
            "page_width": page_width
        }

    return None


def check_images_without_alt(page):
    """Find images that do not have an alt attribute."""

    missing_alt_images = page.locator("img:not([alt])").count()

    if missing_alt_images > 0:
        return {
            "type": "image_missing_alt",
            "severity": "medium",
            "message": (
                "Some images are missing an alt attribute."
            ),
            "count": missing_alt_images
        }

    return None


def inspect_page(page):
    """Run all UI checks and return a structured result."""

    checks = [
        check_page_title,
        check_horizontal_overflow,
        check_images_without_alt
    ]

    findings = []

    for check in checks:
        finding = check(page)

        if finding is not None:
            findings.append(finding)

    return {
        "page_title": page.title(),
        "viewport_width": page.evaluate("window.innerWidth"),
        "issues_found": len(findings),
        "issues": findings
    }
