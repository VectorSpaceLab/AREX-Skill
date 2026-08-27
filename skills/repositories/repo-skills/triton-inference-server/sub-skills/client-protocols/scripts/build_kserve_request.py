#!/usr/bin/env python3
"""Build Triton KServe request descriptors without contacting a live server."""
from __future__ import annotations

import argparse, json


def descriptor(kind: str, model: str | None, input_name: str | None, shape: list[int] | None, datatype: str | None, ready: bool) -> dict:
    if kind == 'health':
        return {'method': 'GET', 'path': '/v2/health/ready' if ready else '/v2/health/live', 'body': None, 'notes': ['Use HTTP 200 as the ready signal.']}
    if kind == 'metadata':
        return {'method': 'GET', 'path': f'/v2/models/{model}', 'body': None, 'notes': ['Inspect server/model metadata before building inference payloads.']}
    if kind == 'config':
        return {'method': 'GET', 'path': f'/v2/models/{model}/config', 'body': None, 'notes': ['Use the generated config to confirm names, shapes, and datatypes.']}
    if kind == 'infer':
        return {
            'method': 'POST',
            'path': f'/v2/models/{model}/infer',
            'body': {
                'inputs': [{'name': input_name, 'shape': shape, 'datatype': datatype, 'parameters': {}}],
                'outputs': []
            },
            'notes': ['This is a request template only; fill data or binary body according to the model and transport.']
        }
    if kind == 'repository-index':
        return {'method': 'GET', 'path': '/v2/repository/index', 'body': None, 'notes': ['Use this for live repository-control debugging.']}
    raise SystemExit(f'unknown kind {kind!r}')


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    h = sub.add_parser('health'); h.add_argument('--kind', dest='health_kind', choices=['ready','live'], default='ready'); h.add_argument('--json', action='store_true')
    m = sub.add_parser('metadata'); m.add_argument('model'); m.add_argument('--json', action='store_true')
    c = sub.add_parser('config'); c.add_argument('model'); c.add_argument('--json', action='store_true')
    i = sub.add_parser('infer'); i.add_argument('model'); i.add_argument('--input-name', required=True); i.add_argument('--shape', nargs='+', type=int, required=True); i.add_argument('--datatype', required=True); i.add_argument('--json', action='store_true')
    r = sub.add_parser('repository-index'); r.add_argument('--json', action='store_true')
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    if a.command == 'health': out = descriptor('health', None, None, None, None, a.health_kind == 'ready')
    elif a.command == 'metadata': out = descriptor('metadata', a.model, None, None, None, False)
    elif a.command == 'config': out = descriptor('config', a.model, None, None, None, False)
    elif a.command == 'infer': out = descriptor('infer', a.model, a.input_name, a.shape, a.datatype, False)
    else: out = descriptor('repository-index', None, None, None, None, False)
    if getattr(a, 'json', False): print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"{out['method']} {out['path']}")
        if out['body'] is not None: print(json.dumps(out['body'], indent=2, sort_keys=True))
        for note in out['notes']: print('note:', note)
    return 0

if __name__ == '__main__': raise SystemExit(main())
