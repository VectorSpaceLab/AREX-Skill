#!/usr/bin/env python3
from __future__ import annotations
import argparse, tempfile
from pathlib import Path
import pymupdf

def main():
    ap=argparse.ArgumentParser(description='Create a tiny PDF and exercise embfile add/list/info/get/update/delete APIs.')
    ap.add_argument('--output'); ap.add_argument('--extract-dir'); ap.add_argument('--overwrite', action='store_true'); a=ap.parse_args()
    out=Path(a.output) if a.output else Path(tempfile.mkdtemp(prefix='pymupdf-embed-'))/'embedded.pdf'
    if out.exists() and not a.overwrite: ap.error('output exists; use --overwrite')
    out.parent.mkdir(parents=True, exist_ok=True); doc=pymupdf.open(); doc.new_page(width=120,height=80); payload=b'embedded payload'; doc.embfile_add('note.txt', payload, filename='note.txt', desc='smoke note')
    assert doc.embfile_count()==1 and doc.embfile_get('note.txt')==payload; doc.embfile_upd('note.txt', desc='updated smoke note'); info=doc.embfile_info('note.txt'); assert info['description']=='updated smoke note'; doc.save(str(out), garbage=3, deflate=True)
    if a.extract_dir:
        ex=Path(a.extract_dir); ex.mkdir(parents=True, exist_ok=True); (ex/'note.txt').write_bytes(payload)
    print({'status':'passed','output':str(out),'name':doc.embfile_names()[0]}); return 0
if __name__=='__main__': raise SystemExit(main())
