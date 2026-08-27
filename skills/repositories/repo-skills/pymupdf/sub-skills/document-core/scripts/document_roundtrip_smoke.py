#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
import pymupdf

def main():
    ap=argparse.ArgumentParser(description='Create and verify a tiny PyMuPDF document-core PDF roundtrip.')
    ap.add_argument('--output-dir'); ap.add_argument('--summary-json')
    args=ap.parse_args(); outdir=Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix='pymupdf-doc-smoke-')); outdir.mkdir(parents=True, exist_ok=True)
    pdf=outdir/'roundtrip.pdf'; doc=pymupdf.open(); page=doc.new_page(width=240,height=120); page.insert_text((36,70),'Document core smoke'); doc.set_metadata({'title':'Document Core Smoke'}); doc.set_toc([[1,'Start',1]]); data=doc.tobytes(garbage=3, deflate=True); doc.save(str(pdf), garbage=3, deflate=True)
    reopened=pymupdf.open(stream=data, filetype='pdf'); assert reopened.page_count==1; assert reopened[0].get_text().strip()=='Document core smoke'; assert reopened.metadata.get('title')=='Document Core Smoke'; assert reopened.get_toc()[0][1]=='Start'
    summary={'status':'passed','pdf':str(pdf),'page_count':reopened.page_count,'text':reopened[0].get_text().strip()}
    sp=Path(args.summary_json) if args.summary_json else outdir/'summary.json'; sp.write_text(json.dumps(summary, indent=2), encoding='utf-8'); print(json.dumps(summary, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
