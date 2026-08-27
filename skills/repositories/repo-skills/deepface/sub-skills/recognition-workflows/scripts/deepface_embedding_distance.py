#!/usr/bin/env python3
"""Compare two precomputed DeepFace embedding JSON arrays without importing DeepFace."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Iterable, List
THRESHOLDS={"VGG-Face":{"cosine":0.68,"euclidean":1.17,"euclidean_l2":1.17,"angular":0.39},"Facenet":{"cosine":0.40,"euclidean":10.0,"euclidean_l2":0.80,"angular":0.33},"Facenet512":{"cosine":0.30,"euclidean":23.56,"euclidean_l2":1.04,"angular":0.35},"ArcFace":{"cosine":0.68,"euclidean":4.15,"euclidean_l2":1.13,"angular":0.39},"SFace":{"cosine":0.593,"euclidean":10.734,"euclidean_l2":1.055,"angular":0.36}}

def load_embedding(path:str)->List[float]:
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if isinstance(data,dict) and 'embedding' in data: data=data['embedding']
    if not isinstance(data,list) or not data or not all(isinstance(x,(int,float)) for x in data):
        raise SystemExit(f'{path} must contain a JSON list of numbers or an object with an embedding list')
    return [float(x) for x in data]

def l2(vec:Iterable[float])->List[float]:
    vals=list(vec); norm=math.sqrt(sum(x*x for x in vals)); return [x/(norm+1e-10) for x in vals]

def distance(a:List[float], b:List[float], metric:str)->float:
    if len(a)!=len(b): raise SystemExit(f'dimension mismatch: {len(a)} vs {len(b)}')
    if metric=='cosine':
        dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b)); return round(1-dot/((na*nb)+1e-10), 6)
    if metric=='euclidean': return round(math.sqrt(sum((x-y)**2 for x,y in zip(a,b))), 6)
    if metric=='euclidean_l2': return distance(l2(a), l2(b), 'euclidean')
    if metric=='angular':
        cos_dist=max(0.0, min(2.0, distance(a,b,'cosine'))); similarity=max(-1.0, min(1.0, 1-cos_dist)); return round(math.acos(similarity)/math.pi, 6)
    raise SystemExit(f'unsupported metric: {metric}')

def main()->int:
    ap=argparse.ArgumentParser(description='Compare two precomputed DeepFace embedding JSON arrays.')
    ap.add_argument('--embedding-a', required=True)
    ap.add_argument('--embedding-b', required=True)
    ap.add_argument('--metric', default='cosine', choices=['cosine','euclidean','euclidean_l2','angular'])
    ap.add_argument('--model', default=None)
    args=ap.parse_args()
    a=load_embedding(args.embedding_a); b=load_embedding(args.embedding_b); d=distance(a,b,args.metric)
    print(json.dumps({'metric':args.metric,'distance':d,'dimensions':len(a)}, indent=2))
    if args.model:
        threshold=THRESHOLDS.get(args.model,{}).get(args.metric)
        print(f'Threshold for {args.model}/{args.metric}: {threshold}; verified={d <= threshold}' if threshold is not None else f'No bundled threshold for {args.model}/{args.metric}.')
    return 0
if __name__=='__main__': raise SystemExit(main())
