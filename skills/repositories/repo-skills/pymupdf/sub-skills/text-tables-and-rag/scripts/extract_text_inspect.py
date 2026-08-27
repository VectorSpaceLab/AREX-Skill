#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pymupdf
MODES={'text','blocks','words','dict','rawdict','html','xml','xhtml','json','rawjson'}
def pages(spec,count):
    if not spec: return list(range(count))
    out=[]
    for t in spec.split(','):
        if '-' in t:
            a,b=map(int,t.split('-',1)); out+=list(range(a,b+1))
        else: out.append(int(t))
    return sorted(set(out))
def clip(s): return pymupdf.Rect([float(x) for x in s.split(',')]) if s else None
def safe(v):
    if isinstance(v, bytes): return {'bytes':len(v)}
    if isinstance(v,(str,int,float,bool)) or v is None: return v
    if isinstance(v,dict): return {str(k):safe(val) for k,val in v.items()}
    if isinstance(v,(list,tuple)): return [safe(x) for x in v]
    return repr(v)
def main():
    ap=argparse.ArgumentParser(description='Inspect PyMuPDF text extraction output for selected pages.')
    ap.add_argument('--input', required=True); ap.add_argument('--mode', choices=sorted(MODES), default='text'); ap.add_argument('--pages'); ap.add_argument('--clip'); ap.add_argument('--sort', action='store_true'); ap.add_argument('--output'); ap.add_argument('--json-summary', action='store_true')
    a=ap.parse_args(); doc=pymupdf.open(a.input); ps=pages(a.pages, doc.page_count); c=clip(a.clip)
    if a.json_summary:
        data={'page_count':doc.page_count,'selected_pages':ps,'mode':a.mode,'pages':[]}
        for p in ps:
            val=doc[p].get_text(a.mode, clip=c, sort=a.sort); data['pages'].append({'page_index':p,'item_count':len(val) if hasattr(val,'__len__') else 0,'preview':str(val)[:300]})
        text=json.dumps(data, indent=2, ensure_ascii=False)
    else:
        vals=[doc[p].get_text(a.mode, clip=c, sort=a.sort) for p in ps]; text='\f\n'.join(map(str, vals)) if isinstance(vals[0], str) else json.dumps(safe(vals), indent=2, ensure_ascii=False)
    if a.output: Path(a.output).parent.mkdir(parents=True, exist_ok=True); Path(a.output).write_text(text, encoding='utf-8')
    else: print(text)
    return 0
if __name__=='__main__': raise SystemExit(main())
