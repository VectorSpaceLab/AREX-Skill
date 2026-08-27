#!/usr/bin/env python3
"""Create a deterministic tiny PDF fixture for PyMuPDF examples."""
from __future__ import annotations
import argparse
from pathlib import Path
import pymupdf

def build_pdf(path: Path, with_table: bool=False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    page = doc.new_page(width=360, height=240)
    page.insert_text((36, 40), "PyMuPDF sample document", fontsize=14)
    page.insert_text((36, 70), "This page contains text, a link target phrase, and simple shapes.", fontsize=10)
    page.draw_rect(pymupdf.Rect(36, 90, 160, 150), color=(0,0,1), width=1)
    if with_table:
        x0, y0, cw, rh = 36, 120, 70, 20
        for r in range(4): page.draw_line((x0, y0+r*rh), (x0+3*cw, y0+r*rh), color=(0,0,0), width=0.5)
        for c in range(4): page.draw_line((x0+c*cw, y0), (x0+c*cw, y0+3*rh), color=(0,0,0), width=0.5)
        for r,row in enumerate([["A","B","C"],["1","2","3"],["4","5","6"]]):
            for c,t in enumerate(row): page.insert_text((x0+c*cw+8, y0+r*rh+14), t, fontsize=9)
    doc.set_metadata({"title":"PyMuPDF Skill Sample","author":"PyMuPDF repo skill"})
    doc.save(str(path), garbage=3, deflate=True)

def main():
    ap=argparse.ArgumentParser(description="Create a tiny deterministic PyMuPDF PDF fixture.")
    ap.add_argument('--output', required=True)
    ap.add_argument('--with-table', action='store_true')
    args=ap.parse_args(); out=Path(args.output)
    if out.suffix.lower()!='.pdf': ap.error('--output must end with .pdf')
    build_pdf(out, args.with_table); print(out); return 0
if __name__=='__main__': raise SystemExit(main())
