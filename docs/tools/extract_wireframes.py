"""Extract the six low-fidelity wireframes (Figures 1.7-1.12) from the design chapter PDF.

The wireframes are embedded as raster images on pages 24-26, two per page, in figure order.
Usage: python docs/tools/extract_wireframes.py
"""
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs" / "reference" / "RPMS__Background_Analysis_and_Design_24550337.pdf"
OUT = ROOT / "docs" / "images" / "wireframes"

NAMES = [
    "fig-1-7-login",
    "fig-1-8-student-dashboard",
    "fig-1-9-proposal",
    "fig-1-10-review-submission",
    "fig-1-11-progress-update",
    "fig-1-12-coordinator-projects",
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    images = []
    for page_no in (23, 24, 25):  # zero-based: pages 24, 25, 26
        page = doc[page_no]
        found = []
        for info in page.get_images(full=True):
            xref = info[0]
            rect = page.get_image_rects(xref)[0]
            found.append((rect.y0, xref))
        images.extend(xref for _, xref in sorted(found))

    if len(images) != len(NAMES):
        raise SystemExit(f"Expected {len(NAMES)} images, found {len(images)}")

    for name, xref in zip(NAMES, images):
        pix = pymupdf.Pixmap(doc, xref)
        if pix.alpha or pix.n > 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        target = OUT / f"{name}.png"
        pix.save(target)
        print(f"{target.relative_to(ROOT)}  {pix.width}x{pix.height}")


if __name__ == "__main__":
    main()
