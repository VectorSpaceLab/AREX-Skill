#!/usr/bin/env python3
import argparse,json,statistics,sys

def select_by_median_proximity(scores, size):
    if not scores: raise ValueError('scores must be non-empty')
    if not isinstance(size,int) or size<1 or size>len(scores): raise ValueError('size must be between 1 and len(scores)')
    values=[]
    for item in scores:
        if 'id' not in item or 'score' not in item: raise ValueError('score records need id and score')
        if not isinstance(item['score'],(int,float)): raise ValueError('score must be numeric')
        values.append(float(item['score']))
    med=float(statistics.median(values))
    ranked=sorted(({'id':str(item['id']),'score':float(item['score']),'distance_to_median':abs(float(item['score'])-med)} for item in scores), key=lambda x:(x['distance_to_median'], x['score'], x['id']))
    return {'median':med,'selected_ids':[item['id'] for item in ranked[:size]],'ranked':ranked}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--size',type=int); p.add_argument('--output'); p.add_argument('--self-test',action='store_true')
    a=p.parse_args(argv)
    if a.self_test:
        out=select_by_median_proximity([{'id':'a','score':0},{'id':'b','score':2},{'id':'c','score':4},{'id':'d','score':10}],2)
        assert out['median']==3.0 and out['selected_ids']==['b','c']; return 0
    out=select_by_median_proximity(json.loads(open(a.input,encoding='utf-8').read()), a.size)
    text=json.dumps(out,indent=2); open(a.output,'w',encoding='utf-8').write(text+'\n') if a.output else print(text)
    return 0
if __name__=='__main__': sys.exit(main())
