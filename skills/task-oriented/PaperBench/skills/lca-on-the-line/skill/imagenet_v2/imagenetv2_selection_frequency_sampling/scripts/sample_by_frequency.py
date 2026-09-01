#!/usr/bin/env python3
import argparse, json
from collections import defaultdict

def _records(payload):
    return payload.get('records', payload) if isinstance(payload, dict) else payload

def sample_records(records, strategy, per_class):
    groups=defaultdict(list)
    for r in records: groups[str(r['class_id'])].append(r)
    sampled=[]; warnings=[]
    for cls in sorted(groups):
        items=sorted(groups[cls], key=lambda r:(-float(r['selection_frequency']), str(r['candidate_id'])))
        if strategy == 'top_images': chosen=items[:per_class]
        elif strategy == 'threshold_0_7': chosen=[r for r in items if float(r['selection_frequency']) >= 0.7][:per_class]
        elif strategy == 'matched_frequency':
            asc=sorted(groups[cls], key=lambda r:(float(r['selection_frequency']), str(r['candidate_id'])))
            if per_class == 1: chosen=[asc[len(asc)//2]]
            else:
                idxs=sorted({round(i*(len(asc)-1)/(per_class-1)) for i in range(per_class)})
                chosen=[asc[i] for i in idxs][:per_class]
        else: raise ValueError('unknown strategy')
        if len(chosen) < per_class: warnings.append(f'{cls} underfilled {len(chosen)}/{per_class}')
        sampled.extend(chosen)
    avg=sum(float(r['selection_frequency']) for r in sampled)/len(sampled) if sampled else 0.0
    return {'schema_version':1,'strategy':strategy,'per_class':per_class,'sampled':sampled,'stats':{'sample_count':len(sampled),'class_count':len(groups),'average_selection_frequency':avg,'warnings':warnings}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--strategy', required=True); ap.add_argument('--per-class', type=int, default=1); ap.add_argument('--output', required=True)
    args=ap.parse_args(); payload=json.load(open(args.input)); res=sample_records(_records(payload), args.strategy, args.per_class); json.dump(res, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
