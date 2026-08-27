#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pymupdf

def main():
    ap=argparse.ArgumentParser(description='Create a small PDF with grid lines, vector drawings, text, and optional preview.')
    ap.add_argument('--output-pdf', required=True); ap.add_argument('--preview-png'); ap.add_argument('--metadata-json'); ap.add_argument('--dpi', type=int, default=144)
    a=ap.parse_args(); pdf=Path(a.output_pdf); pdf.parent.mkdir(parents=True, exist_ok=True)
    doc=pymupdf.open(); page=doc.new_page(width=320,height=220)
    for x in range(40,281,40): page.draw_line((x,40),(x,180),color=(0.7,0.7,0.7),width=.4)
    for y in range(40,181,40): page.draw_line((40,y),(280,y),color=(0.7,0.7,0.7),width=.4)
    page.draw_rect(pymupdf.Rect(60,60,160,120), color=(1,0,0), fill=(1,.9,.9)); page.insert_text((70,95),'Grid sample')
    page.insert_htmlbox(pymupdf.Rect(170,60,270,120), '<b>HTML</b><br/>box', css='* {font-size: 10px;}')
    doc.save(str(pdf), garbage=3, deflate=True); drawings=page.get_drawings()
    report={'pdf':str(pdf),'drawing_count':len(drawings)}
    if a.preview_png:
        pix=page.get_pixmap(dpi=a.dpi); Path(a.preview_png).parent.mkdir(parents=True, exist_ok=True); pix.save(a.preview_png); report['preview_png']=a.preview_png
    if a.metadata_json: Path(a.metadata_json).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
