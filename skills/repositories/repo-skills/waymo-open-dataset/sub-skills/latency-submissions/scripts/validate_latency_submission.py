#!/usr/bin/env python3
"""Validate a WOD latency challenge submission module with tiny fake inputs."""
from __future__ import annotations
import argparse, importlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

def load_module(spec: str):
    path = Path(spec)
    if path.exists():
        module_spec = importlib.util.spec_from_file_location('wod_latency_submission_candidate', path)
        if module_spec is None or module_spec.loader is None: raise ImportError(f'Cannot load {path}')
        mod = importlib.util.module_from_spec(module_spec); sys.modules[module_spec.name]=mod; module_spec.loader.exec_module(mod); return mod
    return importlib.import_module(spec)

def fake_field(name: str):
    base = name[:-2] if name.endswith(('_1','_2')) else name
    if base.endswith('_IMAGE'): return np.zeros((4,4,3), dtype=np.uint8)
    if base.endswith('_INTRINSIC'): return np.zeros((9,), dtype=np.float32)
    if base.endswith('_EXTRINSIC') or base.endswith('_POSE'): return np.eye(4, dtype=np.float32)
    if 'RANGE_IMAGE' in base: return np.zeros((2,3,6), dtype=np.float32)
    if 'CAM_PROJ' in base: return np.zeros((2,3,6), dtype=np.int64)
    if base.endswith('_BEAM_INCLINATION'): return np.zeros((2,), dtype=np.float32)
    if base.endswith('_WIDTH') or base.endswith('_HEIGHT') or base == 'TIMESTAMP': return np.array(1, dtype=np.int64)
    return np.zeros((1,), dtype=np.float32)

def main() -> int:
    parser=argparse.ArgumentParser(description='Validate WOD latency wod_latency_submission contract.')
    parser.add_argument('module', help='Import name or .py file for candidate module.')
    parser.add_argument('--json', action='store_true')
    args=parser.parse_args()
    report={'module': args.module, 'ok': False, 'warnings': []}
    try:
        mod=load_module(args.module)
        fields=list(getattr(mod, 'DATA_FIELDS', getattr(mod, 'DATA_FORMATS', [])))
        if not fields: raise ValueError('Module must define non-empty DATA_FIELDS list')
        if not hasattr(mod, 'DATA_FIELDS') and hasattr(mod, 'DATA_FORMATS'): report['warnings'].append('Used DATA_FORMATS fallback; source evaluator expects DATA_FIELDS.')
        init=getattr(mod, 'initialize_model', None); run=getattr(mod, 'run_model', None)
        if not callable(init) or not callable(run): raise ValueError('Module must define callable initialize_model and run_model')
        init(); data={f: fake_field(f) for f in fields}; out=run(**data)
        if set(out) != {'boxes','scores','classes'}: raise ValueError('run_model must return exactly boxes, scores, classes')
        boxes=np.asarray(out['boxes']); scores=np.asarray(out['scores']); classes=np.asarray(out['classes'])
        if boxes.ndim != 2 or boxes.shape[1] not in (4,7): raise ValueError(f'boxes must have shape N x 4 or N x 7, got {boxes.shape}')
        if scores.shape[0] != boxes.shape[0] or classes.shape[0] != boxes.shape[0]: raise ValueError('scores/classes length must match boxes N')
        report.update({'ok': True, 'data_fields': fields, 'boxes_shape': list(boxes.shape), 'scores_shape': list(scores.shape), 'classes_shape': list(classes.shape)})
    except Exception as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if report.get('ok') else 1
if __name__=='__main__': raise SystemExit(main())
