#!/usr/bin/env python3
import argparse, json, math, sys

def _validate(records):
    if not records:
        raise ValueError('records must be non-empty')
    dim=None; seen=set()
    for rec in records:
        if 'id' not in rec or 'label' not in rec or 'representation' not in rec:
            raise ValueError('each record needs id, label, representation')
        if rec['id'] in seen:
            raise ValueError('record ids must be unique')
        seen.add(rec['id'])
        vec=rec['representation']
        if not isinstance(vec, list) or not vec:
            raise ValueError('representation must be a non-empty list')
        if dim is None: dim=len(vec)
        if len(vec)!=dim: raise ValueError('all representations must have the same dimension')
        for value in vec:
            if not isinstance(value,(int,float)): raise ValueError('representation values must be numeric')

def compute_class_centers(records):
    _validate(records)
    sums={}; counts={}
    for rec in records:
        label=str(rec['label']); vec=[float(x) for x in rec['representation']]
        sums.setdefault(label,[0.0]*len(vec)); counts[label]=counts.get(label,0)+1
        for i,v in enumerate(vec): sums[label][i]+=v
    return {label:[v/counts[label] for v in values] for label,values in sums.items()}

def score_records(records):
    centers=compute_class_centers(records)
    scores=[]
    for rec in records:
        center=centers[str(rec['label'])]
        dist=math.sqrt(sum((float(v)-center[i])**2 for i,v in enumerate(rec['representation'])))
        scores.append({'id':rec['id'],'label':rec['label'],'score':dist})
    return {'centers':centers,'scores':scores}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--output'); p.add_argument('--self-test',action='store_true')
    a=p.parse_args(argv)
    if a.self_test:
        data=[{'id':'a','label':0,'representation':[0,0]},{'id':'b','label':0,'representation':[2,0]},{'id':'c','label':1,'representation':[10,0]}]
        out=score_records(data); assert out['centers']['0']==[1.0,0.0]; assert round(out['scores'][0]['score'],3)==1.0; return 0
    records=json.loads(open(a.input,encoding='utf-8').read())
    out=score_records(records)
    text=json.dumps(out,indent=2)
    open(a.output,'w',encoding='utf-8').write(text+'\n') if a.output else print(text)
    return 0
if __name__=='__main__': sys.exit(main())
