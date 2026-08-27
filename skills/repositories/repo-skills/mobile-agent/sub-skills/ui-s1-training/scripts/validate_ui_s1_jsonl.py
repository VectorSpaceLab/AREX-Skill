#!/usr/bin/env python3
"""Validate UI-S1 GUI trajectory JSONL shape without model calls."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='Validate UI-S1/AndroidControl trajectory JSONL.')
    p.add_argument('--jsonl', required=True); p.add_argument('--require-check-options', action='store_true'); p.add_argument('--write-normalized')
    a=p.parse_args(); errors=[]; warnings=[]; rows=[]
    for i,line in enumerate(Path(a.jsonl).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: obj=json.loads(line)
        except json.JSONDecodeError as e: errors.append(f'line {i}: invalid JSON: {e.msg}'); continue
        rows.append(obj)
        if not isinstance(obj.get('goal'), str) or not obj.get('goal','').strip(): errors.append(f'line {i}: missing goal')
        steps=obj.get('steps')
        if not isinstance(steps, list) or not steps: errors.append(f'line {i}: steps must be non-empty list'); continue
        for j,st in enumerate(steps):
            if not isinstance(st, dict): errors.append(f'line {i} step {j}: step not object'); continue
            if not st.get('screenshot'): errors.append(f'line {i} step {j}: missing screenshot')
            if 'action_content' not in st: errors.append(f'line {i} step {j}: missing action_content')
            elif not isinstance(st['action_content'], dict): errors.append(f'line {i} step {j}: action_content must be object')
            if 'check_options' not in st:
                if a.require_check_options: errors.append(f'line {i} step {j}: missing check_options')
                else:
                    warnings.append(f'line {i} step {j}: check_options missing; can normalize from action_content for SOP-style eval')
                    if isinstance(st.get('action_content'), dict): st['check_options']=dict(st['action_content'])
    if a.write_normalized and not errors:
        Path(a.write_normalized).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')
        print(f'wrote_normalized={a.write_normalized}')
    print(f'rows={len(rows)}')
    print('response_format=<think> optional plus <action>{JSON}</action> required by JsonFormat when thought is enabled')
    for w in warnings: print('WARNING:',w)
    for e in errors: print('ERROR:',e,file=sys.stderr)
    return 2 if errors else 0
if __name__=='__main__': raise SystemExit(main())
