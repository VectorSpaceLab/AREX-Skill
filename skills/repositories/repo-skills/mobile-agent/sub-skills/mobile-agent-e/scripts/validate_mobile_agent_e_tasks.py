#!/usr/bin/env python3
"""Validate Mobile-Agent-E task-list JSON without connecting to Android."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

VALID_TYPES={'single_app','multi_app','web','system','other'}

def main():
    p=argparse.ArgumentParser(description='Validate Mobile-Agent-E tasks_json shape.')
    p.add_argument('--tasks-json', required=True)
    p.add_argument('--allow-bare-list', action='store_true', default=True)
    p.add_argument('--require-apps', action='store_true', default=True)
    a=p.parse_args()
    errors=[]; warnings=[]
    try: obj=json.loads(Path(a.tasks_json).read_text(encoding='utf-8'))
    except Exception as e:
        print(f'ERROR: cannot read/parse JSON: {e}', file=sys.stderr); return 2
    if isinstance(obj, dict):
        tasks=obj.get('tasks')
        if tasks is None: errors.append('object root must contain tasks')
        if 'length' in obj and isinstance(tasks, list) and obj['length'] != len(tasks):
            errors.append(f"length={obj['length']} does not match tasks count {len(tasks)}")
    elif isinstance(obj, list) and a.allow_bare_list:
        tasks=obj; warnings.append('bare list accepted, but object root with length/scenario/tasks is closer to examples')
    else:
        errors.append('root must be object with tasks or a bare list')
        tasks=[]
    if not isinstance(tasks, list) or not tasks:
        errors.append('tasks must be a non-empty list')
    else:
        seen=set()
        for i,t in enumerate(tasks):
            if not isinstance(t, dict): errors.append(f'task {i}: not an object'); continue
            tid=t.get('task_id')
            if not isinstance(tid,str) or not tid.strip(): errors.append(f'task {i}: missing string task_id')
            elif tid in seen: errors.append(f'task {i}: duplicate task_id {tid!r}')
            else: seen.add(tid)
            if not isinstance(t.get('instruction'), str) or not t.get('instruction','').strip(): errors.append(f'task {i}: missing non-empty instruction')
            apps=t.get('apps')
            if a.require_apps and (not isinstance(apps, list) or not all(isinstance(x,str) and x for x in apps)):
                errors.append(f'task {i}: apps must be a non-empty list of strings')
            typ=t.get('type')
            if typ is not None and typ not in VALID_TYPES:
                warnings.append(f'task {i}: uncommon type {typ!r}; examples use single_app or multi_app')
    print(f'tasks={len(tasks) if isinstance(tasks,list) else 0}')
    for w in warnings: print('WARNING:',w)
    for e in errors: print('ERROR:',e,file=sys.stderr)
    return 2 if errors else 0
if __name__=='__main__': raise SystemExit(main())
