#!/usr/bin/env python3
"""Build or optionally send a tiny v1 capability/infer smoke request.

Default mode is dry-run and does not contact a server. Use --send only for a
user-approved local endpoint; this helper never starts a server or controls a
robot.
"""
from __future__ import annotations
import argparse, base64, json, urllib.request

def png_1x1():
    # A valid tiny PNG; deterministic fixture avoids checkout dependencies.
    return base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc000000301010018dd8db40000000049454e44ae426082")).decode()

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--url",default="http://127.0.0.1:7891"); ap.add_argument("--send",action="store_true"); ap.add_argument("--include-state",action="store_true"); a=ap.parse_args()
    payload={"observation":{"prompt":"smoke test; do not execute physical control","images":{"1":png_1x1()}},"sampling":{"num_steps":1,"cfg_scale":1.0,"seed":0}}
    if a.include_state: payload["observation"]["state"]=[0.0]
    print(json.dumps({"url":a.url,"payload":payload,"dry_run":not a.send},indent=2))
    if not a.send: return
    req=urllib.request.Request(a.url.rstrip("/")+"/v1/infer",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=10) as r: print(json.dumps(json.loads(r.read()),indent=2))
if __name__=="__main__": main()
