"""Capture screenshots of the static RPMS pages for the UI design documentation.

Opens each HTML file directly from disk (file://) in the installed Microsoft Edge through
Playwright. The UI files are never modified: interaction states are produced only by
adding a URL fragment, clicking a <summary> or ticking the menu checkbox, and state crops
are taken by clipping the screenshot between the "Mock-up state" markers.

Usage: python docs/tools/capture_screenshots.py
Output: docs/images/ui/*.png and docs/images/ui/states/*.png
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "images" / "ui"
STATES = OUT / "states"

DESKTOP = {"width": 1366, "height": 768}
MOBILE = {"width": 360, "height": 740}

PAGES = {
    "shared-login": "login.html",
    "shared-change-password": "shared/change-password.html",
    "shared-403": "shared/403.html",
    "student-dashboard": "student/dashboard.html",
    "student-project": "student/project.html",
    "student-invite-supervisor": "student/invite-supervisor.html",
    "student-deadlines": "student/deadlines.html",
    "student-proposal": "student/proposal.html",
    "student-progress-reports": "student/progress-reports.html",
    "student-final-report": "student/final-report.html",
    "student-feedback": "student/feedback.html",
    "supervisor-dashboard": "supervisor/dashboard.html",
    "supervisor-invitations": "supervisor/invitations.html",
    "supervisor-students": "supervisor/students.html",
    "supervisor-review-queue": "supervisor/review-queue.html",
    "supervisor-review-submission": "supervisor/review-submission.html",
    "supervisor-review-progress": "supervisor/review-progress.html",
    "coordinator-dashboard": "coordinator/dashboard.html",
    "coordinator-research-period": "coordinator/research-period.html",
    "coordinator-deadlines": "coordinator/deadlines.html",
    "coordinator-guidelines": "coordinator/guidelines.html",
    "coordinator-extensions": "coordinator/extensions.html",
    "coordinator-milestones": "coordinator/milestones.html",
    "coordinator-users": "coordinator/users.html",
    "coordinator-projects": "coordinator/projects.html",
    "coordinator-project-detail": "coordinator/project-detail.html",
}

MOBILE_PAGES = {
    "mobile-login": "login.html",
    "mobile-student-dashboard": "student/dashboard.html",
    "mobile-student-proposal": "student/proposal.html",
    "mobile-coordinator-projects": "coordinator/projects.html",
}

# Segments of <main> separated by the .mock-state markers. Segment 0 is the part above the
# first marker; segment k is the part after marker k. None means "do not save".
STATE_SEGMENTS = {
    "student/project.html": [None, "project-draft", "project-locked"],
    "student/invite-supervisor.html": [None, "invite-draft", "invite-pending", "invite-assigned-history"],
    "student/proposal.html": [None, "proposal-revision", "proposal-blocked", "proposal-no-supervisor",
                              "proposal-approved"],
    "student/progress-reports.html": ["progress-form", "progress-not-open"],
    "student/final-report.html": ["final-report-draft", "final-report-submitted", "final-report-approved"],
}

# Single elements captured on their own: name -> (page, CSS selector)
ELEMENTS = {
    "supervisor-invitation-pending": ("supervisor/invitations.html", "section[aria-labelledby='pending-heading'] article"),
    "supervisor-invitations-past": ("supervisor/invitations.html", "section[aria-labelledby='past-heading']"),
    "student-invite-info": ("student/invite-supervisor.html", "main > .alert--info"),
    "supervisor-review-feedback-form": ("supervisor/review-submission.html", "section[aria-labelledby='feedback-form-heading']"),
    "supervisor-review-progress-forms": ("supervisor/review-progress.html", "main .layout-detail > .stack"),
    "student-deadlines-table": ("student/deadlines.html", "section[aria-labelledby='deadlines-heading']"),
    "coordinator-extensions-form": ("coordinator/extensions.html", "main .layout-detail"),
    "coordinator-extensions-granted": ("coordinator/extensions.html", "section[aria-labelledby='granted-heading']"),
    "coordinator-project-actions": ("coordinator/project-detail.html", "aside[aria-label='Coordinator actions'] section"),
    "supervisor-review-queue-table": ("supervisor/review-queue.html", "main .table-wrap"),
    "student-feedback-v2": ("student/feedback.html", "#fb-proposal-v2"),
    "header-student": ("student/dashboard.html", "header.site-header"),
    "header-supervisor": ("supervisor/dashboard.html", "header.site-header"),
    "header-coordinator": ("coordinator/dashboard.html", "header.site-header"),
}


def url(rel):
    return (ROOT / rel).resolve().as_uri()


def open_page(context, rel, fragment=""):
    page = context.new_page()
    page.goto(url(rel) + fragment, wait_until="load")
    page.wait_for_timeout(150)
    return page


def capture_segments(context, rel, names):
    page = open_page(context, rel)
    boxes = page.evaluate(
        """() => {
            const main = document.querySelector('main');
            const m = main.getBoundingClientRect();
            const sy = window.scrollY;
            const marks = [...main.querySelectorAll(':scope > .mock-state')];
            const cuts = [{start: m.top + sy}];
            marks.forEach(el => {
                const r = el.getBoundingClientRect();
                cuts[cuts.length - 1].end = r.top + sy;
                cuts.push({start: r.bottom + sy});
            });
            const last = main.lastElementChild.getBoundingClientRect();
            cuts[cuts.length - 1].end = last.bottom + sy;
            return {x: m.left, width: m.width, cuts};
        }"""
    )
    if len(boxes["cuts"]) != len(names):
        raise RuntimeError(f"{rel}: expected {len(names)} segments, found {len(boxes['cuts'])}")
    saved = []
    for name, cut in zip(names, boxes["cuts"]):
        if not name:
            continue
        # Start just below a marker and stop 2 px above the next one, so no marker text or
        # dashed divider is included in the crop.
        clip = {
            "x": max(boxes["x"], 0),
            "y": cut["start"] + 2,
            "width": boxes["width"],
            "height": cut["end"] - cut["start"] - 4,
        }
        target = STATES / f"{name}.png"
        page.screenshot(path=str(target), clip=clip, full_page=True)
        saved.append(target)
    page.close()
    return saved


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    STATES.mkdir(parents=True, exist_ok=True)
    saved = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")

        desktop = browser.new_context(viewport=DESKTOP, device_scale_factor=1)

        # 1. Full-page desktop screenshots
        for name, rel in PAGES.items():
            page = open_page(desktop, rel)
            target = OUT / f"{name}.png"
            page.screenshot(path=str(target), full_page=True)
            saved.append(target)
            page.close()

        # 2. Interaction states
        page = open_page(desktop, "coordinator/project-detail.html", "#confirm-delete")
        page.set_viewport_size({"width": 1366, "height": 900})
        page.wait_for_timeout(150)
        target = OUT / "coordinator-project-detail-delete-dialog.png"
        page.screenshot(path=str(target))
        saved.append(target)
        page.close()

        page = open_page(desktop, "coordinator/users.html", "#users-students")
        target = OUT / "coordinator-users-tab-students.png"
        page.screenshot(path=str(target), full_page=True)
        saved.append(target)
        page.close()

        page = open_page(desktop, "student/deadlines.html")
        page.click("details.disclosure > summary")
        page.wait_for_timeout(300)
        target = OUT / "student-deadlines-details-open.png"
        page.locator("main details.disclosure").screenshot(path=str(target))
        saved.append(target)
        page.close()

        page = open_page(desktop, "student/progress-reports.html")
        for summary in page.locator("aside details > summary").all():
            summary.click()
        page.wait_for_timeout(300)
        target = OUT / "student-progress-reports-details-open.png"
        page.locator("aside[aria-label='Previous reports']").screenshot(path=str(target))
        saved.append(target)
        page.close()

        page = open_page(desktop, "coordinator/projects.html")
        page.click("details.disclosure > summary")
        page.wait_for_timeout(300)
        target = OUT / "coordinator-projects-status-guide-open.png"
        page.locator("details.disclosure").screenshot(path=str(target))
        saved.append(target)
        page.close()

        page = open_page(desktop, "supervisor/students.html")
        target = OUT / "supervisor-students-details.png"
        page.locator("main .stack-sm").screenshot(path=str(target))
        saved.append(target)
        page.close()

        # 3. State crops and single elements
        for rel, names in STATE_SEGMENTS.items():
            saved.extend(capture_segments(desktop, rel, names))

        for name, (rel, selector) in ELEMENTS.items():
            page = open_page(desktop, rel)
            target = STATES / f"{name}.png"
            page.locator(selector).first.screenshot(path=str(target))
            saved.append(target)
            page.close()

        desktop.close()

        # 4. Mobile screenshots (360 px CSS width, rendered at 2x for print quality)
        mobile = browser.new_context(viewport=MOBILE, device_scale_factor=2, is_mobile=True, has_touch=True)
        for name, rel in MOBILE_PAGES.items():
            page = open_page(mobile, rel)
            target = OUT / f"{name}.png"
            # Clip to the 360 px viewport width: on pages where an element widens the document
            # (see the gap list in the chapter), a full-page capture would show blank canvas.
            height = page.evaluate("document.documentElement.scrollHeight")
            page.screenshot(path=str(target), full_page=True,
                            clip={"x": 0, "y": 0, "width": MOBILE["width"], "height": height})
            saved.append(target)
            # Shorter version (first two screens) for side-by-side figures in the chapter
            target = OUT / f"{name}-top.png"
            page.screenshot(path=str(target), full_page=True,
                            clip={"x": 0, "y": 0, "width": MOBILE["width"],
                                  "height": min(height, 2 * MOBILE["height"])})
            saved.append(target)
            page.close()

        page = open_page(mobile, "student/dashboard.html")
        page.click("label.nav-toggle__label")
        page.wait_for_timeout(200)
        target = OUT / "mobile-menu-open.png"
        page.screenshot(path=str(target))
        saved.append(target)
        page.close()
        mobile.close()

        browser.close()

    for target in saved:
        print(target.relative_to(ROOT))
    print(f"{len(saved)} images captured")


if __name__ == "__main__":
    main()
