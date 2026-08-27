#!/usr/bin/env python3
"""Validate a small GUI-Critic-R1-style JSONL dataset without model inference."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

VALID_LABELS={'Correct','Incorrect','correct','incorrect'}


def check_row(obj, line_no, base: Path, require_score: bool):
    errors=[]; warnings=[]
    if not isinstance(obj, dict):
        return [f'line {line_no}: row is not an object'], []
    problem=str(obj.get('problem') or obj.get('prompt') or '')
    images=obj.get('images') or obj.get('image') or obj.get('image_path')
    if isinstance(images, str): images=[images]
    if not images or not isinstance(images, list):
        errors.append(f'line {line_no}: images must be a non-empty list or string')
    else:
        for im in images:
            if not isinstance(im, str) or not im:
                errors.append(f'line {line_no}: image entries must be non-empty strings')
            elif im.startswith('..') or '/..' in im.replace('\\','/'):
                errors.append(f'line {line_no}: unsafe relative image path {im!r}')
    sol=obj.get('solution', obj.get('label', obj.get('answer')))
    critic=obj.get('critic_result') or obj.get('response') or ''
    if sol is not None and str(sol) not in VALID_LABELS:
        errors.append(f'line {line_no}: solution/label should be Correct or Incorrect, got {sol!r}')
    if '<image>' not in problem:
        warnings.append(f'line {line_no}: problem text does not include <image> marker')
    for section in ['User instruction', 'Decision']:
        if section not in problem:
            warnings.append(f'line {line_no}: problem text missing section {section!r}')
    if require_score and '<score>' not in str(critic) and '<score>' not in str(sol) and '<score>' not in problem:
        errors.append(f'line {line_no}: missing <score> tag required for scoring')
    elif '<score>' not in str(critic) and '<score>' not in str(sol) and '<score>' not in problem:
        warnings.append(f'line {line_no}: no <score> tag found; online scoring may not parse')
    return errors,warnings


def main():
    p=argparse.ArgumentParser(description='Validate GUI-Critic-R1 JSONL shape safely.')
    p.add_argument('--jsonl', required=True)
    p.add_argument('--require-score-tag', action='store_true')
    p.add_argument('--warn-hard-coded-key', action='store_true', default=True)
    a=p.parse_args()
    path=Path(a.jsonl)
    errors=[]; warnings=[]; count=0
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        count+=1
        try: obj=json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f'line {i}: invalid JSON: {e.msg}')
            continue
        e,w=check_row(obj,i,path.parent,a.require_score_tag)
        errors.extend(e); warnings.extend(w)
    if count==0: errors.append('file has no JSONL rows')
    warnings.append('Before live GUI-Critic scoring, replace sample/hard-coded API keys with environment-variable lookup in private runtime code.')
    print(f'rows={count}')
    for w in warnings: print('WARNING:',w)
    for e in errors: print('ERROR:',e,file=sys.stderr)
    return 2 if errors else 0
if __name__=='__main__': raise SystemExit(main())
