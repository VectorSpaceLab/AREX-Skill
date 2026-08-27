#!/usr/bin/env python3
"""Emit a safe Bindu Gateway /plan JSON request skeleton."""
from __future__ import annotations
import argparse, json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--question', default='Ask the peer for a concise status summary.')
    p.add_argument('--peer-name', default='research')
    p.add_argument('--peer-url', default='http://127.0.0.1:3773')
    p.add_argument('--auth', choices=['none','bearer_env','did_signed'], default='none')
    p.add_argument('--token-env-var')
    args=p.parse_args()
    auth={'type': args.auth}
    if args.auth=='bearer_env': auth['envVar']=args.token_env_var or 'PEER_BEARER_TOKEN'
    if args.auth=='did_signed' and args.token_env_var: auth['tokenEnvVar']=args.token_env_var
    req={'question': args.question, 'agents':[{'name':args.peer_name,'endpoint':args.peer_url,'auth':auth,'skills':[{'id':'status','description':'Return concise status or answer text.','outputModes':['text/plain']}]}], 'preferences': {'timeout_ms':60000,'max_steps':5}}
    print(json.dumps(req, indent=2, sort_keys=True))
if __name__=='__main__': main()
