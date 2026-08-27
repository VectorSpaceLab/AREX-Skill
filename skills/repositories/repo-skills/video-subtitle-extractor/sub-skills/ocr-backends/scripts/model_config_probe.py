#!/usr/bin/env python3
"""Report VSE PP-OCRv5 language/mode model mapping without running OCR."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

LATIN = {'af','az','bs','cs','cy','da','de','es','et','fr','ga','hr','hu','id','is','it','ku','la','lt','lv','mi','ms','mt','nl','no','oc','pi','pl','pt','ro','rs_latin','sk','sl','sq','sv','sw','tl','tr','uz','vi','latin','german','french','fi','eu','gl','lb','rm','ca','qu'}
ARABIC = {'ar','fa','ug','ur','ps','sd','bal'}
CYRILLIC = {'ru','rs_cyrillic','be','bg','uk','mn','abq','ady','kbd','ava','dar','inh','che','lbe','lez','tab','cyrillic','sr','kk','ky','tg','mk','tt','cv','ba','mhr','mo','udm','kv','os','bua','xal','tyv','sah','kaa'}
DEVANAGARI = {'hi','mr','ne','bh','mai','ang','bho','mah','sck','new','gom','sa','bgc','devanagari'}

def rec_dir(lang: str, mode: str) -> str | None:
    if mode == 'fast' and lang in {'ch','chinese_cht','en','japan'}:
        return 'PP-OCRv5_mobile_rec_infer'
    if lang in {'ch','chinese_cht','japan','en'}:
        return 'PP-OCRv5_server_rec_infer'
    if lang == 'korean': return 'korean_PP-OCRv5_mobile_rec_infer'
    if lang in LATIN: return 'latin_PP-OCRv5_mobile_rec_infer'
    if lang in ARABIC: return 'arabic_PP-OCRv5_mobile_rec_infer'
    if lang in CYRILLIC: return 'cyrillic_PP-OCRv5_mobile_rec_infer'
    if lang in DEVANAGARI: return 'devanagari_PP-OCRv5_mobile_rec_infer'
    if lang == 'th': return 'th_PP-OCRv5_mobile_rec_infer'
    if lang == 'el': return 'el_PP-OCRv5_mobile_rec_infer'
    return None

def read_model_name(path: Path):
    yml = path / 'inference.yml'
    if not yml.exists(): return None
    for line in yml.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.strip().startswith('model_name:'):
            return line.split(':',1)[1].strip().strip('"\'')
    return None

def main() -> int:
    ap=argparse.ArgumentParser(description='Inspect VSE bundled PP-OCRv5 model mapping without importing PaddleOCR.')
    ap.add_argument('--repo-root', default='.', help='VSE source checkout containing backend/models/V5.')
    ap.add_argument('--languages', nargs='+', default=['ch','en','japan','korean','ar','ru','de','es','vi','th','el'])
    ap.add_argument('--modes', nargs='+', choices=['fast','auto','accurate'], default=['fast','auto','accurate'])
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    base=Path(args.repo_root)/'backend'/'models'/'V5'
    rows=[]
    for lang in args.languages:
        for mode in args.modes:
            det='PP-OCRv5_mobile_det_infer' if mode=='fast' and (base/'PP-OCRv5_mobile_det_infer').exists() else 'PP-OCRv5_server_det_infer'
            rec=rec_dir(lang, mode)
            rows.append({'language':lang,'mode':mode,'det_dir':det,'det_exists':(base/det).exists(),'det_model_name':read_model_name(base/det),'rec_dir':rec,'rec_exists':bool(rec and (base/rec).exists()),'rec_model_name':read_model_name(base/rec) if rec else None})
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for r in rows:
            print(f"{r['language']:12} {r['mode']:8} det={r['det_dir']} ({'ok' if r['det_exists'] else 'missing'}) rec={r['rec_dir']} ({'ok' if r['rec_exists'] else 'missing'})")
    return 0
if __name__=='__main__':
    raise SystemExit(main())
