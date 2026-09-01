#!/usr/bin/env python3
import argparse,json,statistics,sys

def build_extreme_policies(scores, size):
    ordered=sorted(scores, key=lambda x:(float(x['score']), str(x['id'])))
    low=ordered[:size]
    high=ordered[-size:]
    half=size//2; rem=size-half
    two=ordered[:half]+ordered[-rem:]
    return {'center_close':[str(x['id']) for x in low], 'far_from_center':[str(x['id']) for x in high], 'two_end':[str(x['id']) for x in two]}

def evaluate_policies(scores, policies):
    if not scores: raise ValueError('scores required')
    by_id={str(x['id']):x for x in scores}
    full_values=[float(x['score']) for x in scores]
    median=statistics.median(full_values)
    full_spread=max(full_values)-min(full_values) or 1.0
    out={'median':median,'policies':{}}
    for name, ids in policies.items():
        vals=[float(by_id[str(i)]['score']) for i in ids]
        labels={str(by_id[str(i)].get('label','')) for i in ids}
        mean=sum(vals)/len(vals)
        spread=(max(vals)-min(vals)) if len(vals)>1 else 0.0
        centrality=1.0-(abs(mean-median)/full_spread)
        diversity=spread/full_spread
        target_diversity=0.35
        diversity_balance=1.0-abs(diversity-target_diversity)
        balance=0.7*centrality+0.25*diversity_balance+0.03*len(labels)
        out['policies'][name]={'size':len(ids),'mean_score':mean,'score_spread':spread,'class_count':len(labels),'centrality':centrality,'diversity':diversity,'diversity_balance':diversity_balance,'balance_score':balance}
    moderate=out['policies'].get('moderate',{}).get('balance_score')
    extremes=[v['balance_score'] for k,v in out['policies'].items() if k!='moderate']
    out['moderate_selection_advantage']=(moderate-max(extremes)) if moderate is not None and extremes else 0.0
    return out

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--policies'); p.add_argument('--output'); p.add_argument('--self-test',action='store_true')
    a=p.parse_args(argv)
    if a.self_test:
        scores=[{'id':str(i),'label':i%2,'score':s} for i,s in enumerate([0,1,4,5,6,9,10])]
        policies=build_extreme_policies(scores,3); policies['moderate']=['2','3','4']
        out=evaluate_policies(scores,policies); assert out['moderate_selection_advantage']>0; return 0
    scores=json.loads(open(a.input,encoding='utf-8').read()); policies=json.loads(open(a.policies,encoding='utf-8').read())
    out=evaluate_policies(scores,policies); text=json.dumps(out,indent=2)
    open(a.output,'w',encoding='utf-8').write(text+'\n') if a.output else print(text)
    return 0
if __name__=='__main__': sys.exit(main())
