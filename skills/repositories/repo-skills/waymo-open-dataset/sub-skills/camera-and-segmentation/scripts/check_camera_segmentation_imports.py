#!/usr/bin/env python3
"""Check WOD camera and segmentation optional imports."""
from __future__ import annotations
import argparse, importlib, json
from importlib import metadata

def probe(name):
    try:
        mod=importlib.import_module(name); return {'ok': True, 'file': getattr(mod,'__file__',None)}
    except Exception as exc:
        return {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

def main() -> int:
    parser=argparse.ArgumentParser(description='Check WOD camera/segmentation optional imports.')
    parser.add_argument('--json', action='store_true')
    args=parser.parse_args()
    mods=['waymo_open_dataset.wdl_limited.camera.ops.py_camera_model_ops','waymo_open_dataset.utils.camera_segmentation_utils','waymo_open_dataset.wdl_limited.camera_segmentation.camera_segmentation_metrics']
    result={'distribution': None, 'modules': {m: probe(m) for m in mods}}
    try: result['distribution']=metadata.version('waymo-open-dataset-tf-2-12-0')
    except metadata.PackageNotFoundError: pass
    result['ok']=all(v['ok'] for k,v in result['modules'].items() if not k.endswith('camera_segmentation_metrics'))
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
