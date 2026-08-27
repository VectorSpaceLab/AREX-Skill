#!/usr/bin/env python3
"""Validate PC-Agent config shape without printing secrets."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

SECRET_KEYS={'token','api_token','OCR_ACCESS_KEY_ID','OCR_ACCESS_KEY_SECRET','key','secret'}

def redacted(v):
    s=str(v)
    return '<set>' if s and s not in {'<REDACTED>','sk-...'} else '<placeholder-or-empty>'

def main():
    p=argparse.ArgumentParser(description='Validate PC-Agent config.json fields safely.')
    p.add_argument('--config', required=True)
    p.add_argument('--require-ocr-api', action='store_true')
    a=p.parse_args()
    errors=[]; warnings=[]
    try: obj=json.loads(Path(a.config).read_text(encoding='utf-8'))
    except Exception as e:
        print(f'ERROR: cannot parse config: {e}', file=sys.stderr); return 2
    for k in ['vl_model_name','llm_model_name','url','token']:
        if not isinstance(obj.get(k), str) or not obj.get(k): errors.append(f'missing non-empty {k}')
    if obj.get('token') in {'sk-...','<REDACTED>',''}:
        warnings.append('token is a placeholder/redacted value; live run needs a private token')
    url=obj.get('url','')
    if url and not (url.startswith('http://') or url.startswith('https://')):
        errors.append('url should be an http(s) endpoint')
    for key in ['OCR_ACCESS_KEY_ID','OCR_ACCESS_KEY_SECRET']:
        if key not in obj:
            msg=f'{key} missing; OCR API mode needs it or use local OCR/fallback'
            (errors if a.require_ocr_api else warnings).append(msg)
    print('fields:')
    for k in sorted(obj):
        if k in SECRET_KEYS or 'TOKEN' in k.upper() or 'KEY' in k.upper() or 'SECRET' in k.upper():
            print(f'  {k}: {redacted(obj[k])}')
        else:
            print(f'  {k}: {obj[k]}')
    for w in warnings: print('WARNING:',w)
    for e in errors: print('ERROR:',e,file=sys.stderr)
    return 2 if errors else 0
if __name__=='__main__': raise SystemExit(main())
