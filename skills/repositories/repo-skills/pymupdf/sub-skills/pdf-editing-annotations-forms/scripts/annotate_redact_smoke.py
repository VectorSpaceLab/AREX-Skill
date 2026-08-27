#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pymupdf

def main():
    ap=argparse.ArgumentParser(description='Create a tiny PDF, add annotations, redact a search hit, save, reopen, and verify.')
    ap.add_argument('--output', required=True); ap.add_argument('--overwrite', action='store_true'); a=ap.parse_args(); out=Path(a.output)
    if out.exists() and not a.overwrite: ap.error('output exists; use --overwrite')
    out.parent.mkdir(parents=True, exist_ok=True)
    secret='SECRET'; doc=pymupdf.open(); p=doc.new_page(width=260,height=140); p.insert_text((36,70), f'Keep this text but remove {secret}.')
    for r in p.search_for('Keep'): p.add_highlight_annot(r)
    hits=p.search_for(secret); assert hits, 'secret text was not searchable before redaction'
    for r in hits: p.add_redact_annot(r, fill=(0,0,0))
    assert p.apply_redactions(); doc.save(str(out), garbage=4, deflate=True)
    reopened=pymupdf.open(str(out)); txt=reopened[0].get_text(); assert secret not in txt
    print({'status':'passed','output':str(out),'remaining_text':txt.strip()}); return 0
if __name__=='__main__': raise SystemExit(main())
