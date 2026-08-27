#!/usr/bin/env python3
"""Inspect WOD metric imports and a tiny metric config breakdown."""
from __future__ import annotations
import argparse, json

def main() -> int:
    parser=argparse.ArgumentParser(description='Inspect WOD metric config helpers.')
    parser.add_argument('--json', action='store_true')
    args=parser.parse_args()
    result={}
    try:
        import tensorflow as tf
        from waymo_open_dataset.metrics.ops import py_metrics_ops
        from waymo_open_dataset.metrics.python import config_util_py
        from waymo_open_dataset.protos import breakdown_pb2, metrics_pb2
        config=metrics_pb2.Config(); config.breakdown_generator_ids.append(breakdown_pb2.Breakdown.ONE_SHARD); config.difficulties.add()
        result={'ok': True, 'tensorflow': tf.__version__, 'py_metrics_ops_file': getattr(py_metrics_ops,'__file__',None), 'breakdown_names': config_util_py.get_breakdown_names_from_config(config), 'gpu_devices': [str(g) for g in tf.config.list_physical_devices('GPU')]}
    except Exception as exc:
        result={'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result.get('ok') else 1
if __name__=='__main__': raise SystemExit(main())
