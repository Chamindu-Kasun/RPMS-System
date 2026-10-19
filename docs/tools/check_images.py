"""Check that every captured image exists, opens, and is not blank.

An image counts as blank if it has fewer than 8 distinct colours or is smaller than 50 px.
Usage: python docs/tools/check_images.py
"""
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
IMAGES = ROOT / "docs" / "images"


def main():
    files = sorted(IMAGES.rglob("*.png"))
    failed = []
    for f in files:
        try:
            pix = pymupdf.Pixmap(str(f))
            colours = pix.color_count()
            ok = pix.width >= 50 and pix.height >= 50 and colours >= 8
            status = "ok" if ok else "BLANK?"
            print(f"{status:7} {f.relative_to(ROOT)}  {pix.width}x{pix.height}  colours={colours}")
        except Exception as exc:  # unreadable file
            ok = False
            print(f"ERROR   {f.relative_to(ROOT)}  {exc}")
        if not ok:
            failed.append(f)
    print(f"\n{len(files)} images checked, {len(failed)} failed")
    for f in failed:
        print("  FAILED:", f.relative_to(ROOT))


if __name__ == "__main__":
    main()
