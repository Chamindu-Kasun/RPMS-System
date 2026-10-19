"""Check the PDF exported from the Word document.

- Every figure and table caption appears in the body, once, in sequence.
- Every figure caption sits on a page that also holds an image (image and caption together).
- The contents lists were filled in by Word (no placeholder text left).
- Saves small page previews to the scratch folder given as the first argument (optional).

Usage: python docs/tools/check_pdf.py [preview_dir]
"""
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs" / "RPMS_UI_Design_Documentation.pdf"
CAPTION = re.compile(r"^(Figure|Table) 2\.(\d+): ")


def main():
    doc = pymupdf.open(PDF)
    preview = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    problems = []
    captions = {"Figure": [], "Table": []}
    placeholder = 0
    body_started = False

    for pno, page in enumerate(doc, start=1):
        text = page.get_text()
        if "Update Field" in text:
            placeholder += 1
        if (not body_started and re.search(r"^2\.1 Introduction\s*$", text, re.M)
                and "Contents" not in text and "List of" not in text):
            body_started = True
        if not body_started:
            continue
        has_image = bool(page.get_images())
        for line in text.splitlines():
            m = CAPTION.match(line.strip())
            if m:
                kind, num = m.group(1), int(m.group(2))
                captions[kind].append((num, pno))
                if kind == "Figure" and not has_image:
                    problems.append(f"Figure 2.{num} caption on page {pno} has no image on that page")
        if preview:
            preview.mkdir(parents=True, exist_ok=True)
            page.get_pixmap(dpi=45).save(preview / f"p{pno:03d}.png")

    for kind, items in captions.items():
        nums = [n for n, _ in items]
        if nums != list(range(1, len(nums) + 1)):
            problems.append(f"{kind} captions out of sequence or duplicated: {nums}")
        print(f"{kind}s found in body: {len(nums)}")
    if placeholder:
        problems.append(f"{placeholder} page(s) still show a field placeholder")
    print(f"Pages: {doc.page_count}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
    else:
        print("PDF check OK")


if __name__ == "__main__":
    main()
