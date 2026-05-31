#!/usr/bin/env python3
"""Render PDF pages to PNG files for visual inspection."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--scale", type=float, default=1.8)
    args = parser.parse_args()

    pdf = args.pdf if args.pdf.is_absolute() else ROOT / args.pdf
    pdf = pdf.resolve()
    if not pdf.exists():
        raise FileNotFoundError(pdf)

    output_dir = ROOT / "tmp" / "pdfs" / pdf.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_page in output_dir.glob("page-*.png"):
        old_page.unlink()

    document = fitz.open(pdf)
    for index, page in enumerate(document, 1):
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(args.scale, args.scale),
            alpha=False,
        )
        output = output_dir / f"page-{index:02d}.png"
        pixmap.save(output)
        print(output)

    print(f"Rendered {len(document)} pages from {pdf}")


if __name__ == "__main__":
    main()
