#!/usr/bin/env python3
"""Probe Paddle and ONNX backend visibility for VSE."""
from __future__ import annotations
import argparse, json, platform

def main() -> int:
    ap=argparse.ArgumentParser(description='Read-only Paddle/ONNX backend probe for VSE environments.')
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    result={'platform':platform.platform(),'paddle':{},'onnxruntime':{}}
    try:
        import paddle  # type: ignore
        result['paddle']={'version':getattr(paddle,'__version__',None),'compiled_with_cuda':bool(paddle.is_compiled_with_cuda())}
        if result['paddle']['compiled_with_cuda']:
            try: result['paddle']['cuda_places']=len(paddle.static.cuda_places())
            except Exception as exc: result['paddle']['cuda_error']=str(exc)
    except Exception as exc:
        result['paddle']={'error':type(exc).__name__+': '+str(exc)}
    try:
        import onnxruntime as ort  # type: ignore
        result['onnxruntime']={'providers':ort.get_available_providers()}
    except Exception as exc:
        result['onnxruntime']={'error':type(exc).__name__+': '+str(exc)}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print('Platform:', result['platform'])
        print('Paddle:', result['paddle'])
        print('ONNX Runtime:', result['onnxruntime'])
    return 0
if __name__=='__main__':
    raise SystemExit(main())
