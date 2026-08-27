#!/usr/bin/env python3
"""Build or send simple DeepFace API requests. Dry-run is the safe default."""
from __future__ import annotations
import argparse, json, shlex
from urllib.parse import urljoin
ENDPOINT_KEYS={'represent':['img'],'verify':['img1','img2'],'analyze':['img'],'register':['img'],'search':['img'],'build/index':[]}

def main()->int:
    ap=argparse.ArgumentParser(description='Build dry-run curl commands for DeepFace API requests.')
    ap.add_argument('--base-url', default='http://localhost:5005')
    ap.add_argument('--endpoint', required=True, choices=sorted(ENDPOINT_KEYS))
    ap.add_argument('--token')
    ap.add_argument('--img')
    ap.add_argument('--img1')
    ap.add_argument('--img2')
    ap.add_argument('--model-name', default=None)
    ap.add_argument('--detector-backend', default=None)
    ap.add_argument('--actions', default=None)
    ap.add_argument('--dry-run', action='store_true', default=True)
    ap.add_argument('--send', action='store_true')
    args=ap.parse_args(); payload={}
    for key in ENDPOINT_KEYS[args.endpoint]:
        value=getattr(args, key.replace('/','_'), None)
        if value is None: raise SystemExit(f'--{key} is required for /{args.endpoint}')
        payload[key]=value
    if args.model_name: payload['model_name']=args.model_name
    if args.detector_backend: payload['detector_backend']=args.detector_backend
    if args.actions: payload['actions']=[x.strip() for x in args.actions.split(',') if x.strip()]
    url=urljoin(args.base_url.rstrip('/')+'/', args.endpoint)
    headers={'Content-Type':'application/json'}
    if args.token: headers['Authorization']=f'Bearer {args.token}'
    curl_parts=['curl','-X','POST',shlex.quote(url)]
    for key,value in headers.items(): curl_parts.extend(['-H', shlex.quote(f'{key}: {value}')])
    curl_parts.extend(['-d', shlex.quote(json.dumps(payload))])
    print(' '.join(curl_parts)); print(json.dumps(payload, indent=2))
    if args.send:
        import requests
        response=requests.post(url, json=payload, headers={k:v for k,v in headers.items() if k!='Content-Type'}, timeout=60)
        print('status', response.status_code); print(response.text)
        return 0 if response.ok else 1
    return 0
if __name__=='__main__': raise SystemExit(main())
