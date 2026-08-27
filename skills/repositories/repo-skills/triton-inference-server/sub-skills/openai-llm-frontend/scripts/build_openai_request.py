#!/usr/bin/env python3
"""Build Triton OpenAI-compatible /v1 request payloads without sending them."""
from __future__ import annotations
import argparse, json


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='kind', required=True)
    models=sub.add_parser('models'); models.add_argument('--json', action='store_true')
    c=sub.add_parser('chat'); c.add_argument('--model', required=True); c.add_argument('--message', default='Say this is a test.'); c.add_argument('--stream', action='store_true'); c.add_argument('--max-tokens', type=int, default=64); c.add_argument('--json', action='store_true')
    t=sub.add_parser('completion'); t.add_argument('--model', required=True); t.add_argument('--prompt', default='Machine learning is'); t.add_argument('--stream', action='store_true'); t.add_argument('--max-tokens', type=int, default=64); t.add_argument('--json', action='store_true')
    e=sub.add_parser('embedding'); e.add_argument('--model', required=True); e.add_argument('--input', default='hello world'); e.add_argument('--json', action='store_true')
    l=sub.add_parser('load-model'); l.add_argument('model'); l.add_argument('--json', action='store_true')
    u=sub.add_parser('unload-model'); u.add_argument('model'); u.add_argument('--json', action='store_true')
    p.add_argument('--json', action='store_true')
    a=p.parse_args()
    if a.kind=='models': out={'method':'GET','path':'/v1/models','body':None}
    elif a.kind=='chat': out={'method':'POST','path':'/v1/chat/completions','body':{'model':a.model,'messages':[{'role':'user','content':a.message}],'max_tokens':a.max_tokens,'stream':a.stream}}
    elif a.kind=='completion': out={'method':'POST','path':'/v1/completions','body':{'model':a.model,'prompt':a.prompt,'max_tokens':a.max_tokens,'stream':a.stream}}
    elif a.kind=='embedding': out={'method':'POST','path':'/v1/embeddings','body':{'model':a.model,'input':a.input}}
    elif a.kind=='load-model': out={'method':'POST','path':f'/v1/models/{a.model}/load','body':{}}
    else: out={'method':'POST','path':f'/v1/models/{a.model}/unload','body':{}}
    out['notes']=['OpenAI-compatible request template only; send to the OpenAI frontend port, not KServe /v2.']
    if getattr(a, 'json', False): print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(out['method'], out['path'])
        if out['body'] is not None: print(json.dumps(out['body'], indent=2, sort_keys=True))
        for n in out['notes']: print('note:', n)
    return 0
if __name__=='__main__': raise SystemExit(main())
