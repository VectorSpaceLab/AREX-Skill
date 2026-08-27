#!/usr/bin/env python3
"""Create or check a tiny WOD latency result-directory fixture."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

def write_fixture(root: Path, mode: str):
    d=root/'ctx'/'123456'; d.mkdir(parents=True, exist_ok=True)
    boxes=np.array([[1,2,3,4,5,6,0.1]], dtype=np.float32) if mode=='3d' else np.array([[2,2,4,5]], dtype=np.float32)
    np.save(d/'boxes.npy', boxes); np.save(d/'scores.npy', np.array([0.9], dtype=np.float32)); np.save(d/'classes.npy', np.array([1], dtype=np.uint8))
    (d/'input_fields.txt').write_text('FRONT_IMAGE' if mode=='2d' else 'TOP_RANGE_IMAGE_FIRST_RETURN')
    return d

def check(root: Path):
    problems=[]; count=0
    for d in root.glob('*/*'):
        if d.is_dir():
            count+=1
            for name in ['boxes.npy','scores.npy','classes.npy']:
                if not (d/name).exists(): problems.append(f'missing {d/name}')
    return {'frame_dirs': count, 'problems': problems, 'ok': not problems and count>0}

def main() -> int:
    parser=argparse.ArgumentParser(description='Create/check tiny WOD latency result fixture.')
    parser.add_argument('root', type=Path)
    parser.add_argument('--mode', choices=['2d','3d'], default='3d')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--json', action='store_true')
    args=parser.parse_args()
    if not args.check_only: write_fixture(args.root, args.mode)
    result=check(args.root); result['root']=str(args.root)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
