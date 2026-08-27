#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pymupdf

def rect(s): return pymupdf.Rect([float(x) for x in s.split(',')])
def main():
    ap=argparse.ArgumentParser(description='Render a single document page preview with PyMuPDF Page.get_pixmap().')
    ap.add_argument('--input', required=True); ap.add_argument('--page', type=int, default=0); ap.add_argument('--dpi', type=int, default=150); ap.add_argument('--clip'); ap.add_argument('--alpha', action='store_true'); ap.add_argument('--no-annots', action='store_true'); ap.add_argument('--colorspace', choices=['rgb','gray','cmyk'], default='rgb'); ap.add_argument('--output', required=True); ap.add_argument('--jpg-quality', type=int, default=95)
    a=ap.parse_args(); cs={'rgb':pymupdf.csRGB,'gray':pymupdf.csGRAY,'cmyk':pymupdf.csCMYK}[a.colorspace]
    doc=pymupdf.open(a.input); page=doc[a.page]; pix=page.get_pixmap(dpi=a.dpi, clip=rect(a.clip) if a.clip else None, alpha=a.alpha, annots=not a.no_annots, colorspace=cs)
    out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); pix.save(str(out), jpg_quality=a.jpg_quality); print(out); return 0
if __name__=='__main__': raise SystemExit(main())
