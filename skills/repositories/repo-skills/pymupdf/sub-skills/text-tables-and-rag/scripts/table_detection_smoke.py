#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
import pymupdf

def make_pdf(path):
    doc=pymupdf.open(); page=doc.new_page(width=300,height=180); x0,y0,cw,rh=40,50,60,24
    for r in range(4): page.draw_line((x0,y0+r*rh),(x0+3*cw,y0+r*rh),color=(0,0,0),width=0.7)
    for c in range(4): page.draw_line((x0+c*cw,y0),(x0+c*cw,y0+3*rh),color=(0,0,0),width=0.7)
    for r,row in enumerate([['A','B','C'],['1','2','3'],['4','5','6']]):
        for c,t in enumerate(row): page.insert_text((x0+c*cw+8,y0+r*rh+16),t,fontsize=10)
    doc.save(str(path), garbage=3, deflate=True)

def main():
    ap=argparse.ArgumentParser(description='Smoke-test PyMuPDF Page.find_tables().')
    ap.add_argument('--input'); ap.add_argument('--output-dir'); ap.add_argument('--pages'); ap.add_argument('--strategy', choices=['lines','lines_strict','text'], default='lines_strict'); ap.add_argument('--use-layout', action='store_true'); ap.add_argument('--no-markdown', action='store_true')
    a=ap.parse_args(); out=Path(a.output_dir) if a.output_dir else Path(tempfile.mkdtemp(prefix='pymupdf-table-')); out.mkdir(parents=True, exist_ok=True)
    inp=Path(a.input) if a.input else out/'synthetic-table.pdf';
    if not a.input: make_pdf(inp)
    doc=pymupdf.open(str(inp)); selected=range(doc.page_count) if not a.pages else [int(x) for x in a.pages.split(',')]
    res=[]
    for pno in selected:
        tabs=doc[pno].find_tables(strategy=a.strategy, use_layout=a.use_layout)
        for i,t in enumerate(tabs.tables):
            rec={'page_index':pno,'table_index':i,'rows':len(t.extract()),'columns':max((len(r) for r in t.extract()), default=0)}
            if not a.no_markdown:
                md=t.to_markdown(); rec['markdown_preview']=md[:500]; (out/f'page_{pno:04d}_table_{i:02d}.md').write_text(md, encoding='utf-8')
            res.append(rec)
    report={'status':'passed' if res else 'no_tables_detected','input':str(inp),'tables':res}; (out/'tables_summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8'); print(json.dumps(report, indent=2)); return 0 if res else 2
if __name__=='__main__': raise SystemExit(main())
