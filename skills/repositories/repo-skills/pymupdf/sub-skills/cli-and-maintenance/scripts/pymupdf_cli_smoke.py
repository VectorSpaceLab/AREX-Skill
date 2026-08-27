#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
import pymupdf

def make(path, text):
    doc=pymupdf.open(); p=doc.new_page(width=200,height=100); p.insert_text((36,60), text); doc.save(str(path), garbage=3, deflate=True)
def run(cmd):
    cp=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20); return {'cmd':cmd,'returncode':cp.returncode,'stdout':cp.stdout[:300],'stderr':cp.stderr[:300]}
def main():
    ap=argparse.ArgumentParser(description='Generate tiny PDFs and run safe PyMuPDF CLI help/show/gettext/clean/join smoke checks.')
    ap.add_argument('--out-dir', required=True); ap.add_argument('--entry', choices=['module','console','both'], default='module'); ap.add_argument('--force', action='store_true'); ap.add_argument('--json', action='store_true')
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True, exist_ok=True); a_pdf=out/'a.pdf'; b_pdf=out/'b.pdf'; make(a_pdf,'CLI smoke A'); make(b_pdf,'CLI smoke B')
    base=[sys.executable,'-m','pymupdf'] if a.entry!='console' else ['pymupdf']
    cmds=[base+['--help'], base+['show','-metadata',str(a_pdf)], base+['gettext','-output',str(out/'a.txt'),str(a_pdf)], base+['clean',str(a_pdf),str(out/'clean.pdf')], base+['join','-output',str(out/'joined.pdf'),str(a_pdf),str(b_pdf)]]
    results=[run(c) for c in cmds]; status='passed' if all(r['returncode']==0 for r in results) else 'failed'; summary={'status':status,'results':results}; (out/'smoke-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    if a.json: print(json.dumps(summary, indent=2))
    else: print(status)
    return 0 if status=='passed' else 2
if __name__=='__main__': raise SystemExit(main())
