#!/usr/bin/env python3
"""Inspect installed Triton frontend option defaults without starting a server."""
from __future__ import annotations
import argparse, json


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    try:
        import tritonserver
        from tritonfrontend import KServeHttp, KServeGrpc, Metrics
    except Exception as exc:
        payload = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
        print(json.dumps(payload, indent=2) if a.json else payload['error'])
        return 1
    payload = {
        'ok': True,
        'tritonserver_version': getattr(tritonserver, '__version__', None),
        'kserve_http_options': KServeHttp.Options().__dict__,
        'kserve_grpc_options': KServeGrpc.Options().__dict__,
        'metrics_options': Metrics.Options().__dict__,
        'exports': [name for name in ('KServeHttp', 'KServeGrpc', 'Metrics') if hasattr(__import__('tritonfrontend'), name)],
    }
    print(json.dumps(payload, indent=2, sort_keys=True) if a.json else payload)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
