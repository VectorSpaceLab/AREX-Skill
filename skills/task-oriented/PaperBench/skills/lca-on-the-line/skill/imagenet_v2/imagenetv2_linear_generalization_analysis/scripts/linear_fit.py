#!/usr/bin/env python3
import argparse, json

def analyze_pairs(pairs):
    if len(pairs) < 2: raise ValueError('need at least two model pairs')
    xs=[float(p['original_accuracy']) for p in pairs]; ys=[float(p['new_accuracy']) for p in pairs]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    den=sum((x-mx)**2 for x in xs)
    slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den if den else 0.0
    intercept=my-slope*mx
    gaps=[x-y for x,y in zip(xs,ys)]
    agree=total=0
    for i in range(len(pairs)):
        for j in range(i+1,len(pairs)):
            total += 1
            agree += ((xs[i]-xs[j])*(ys[i]-ys[j]) >= 0)
    return {'model_count':len(pairs),'slope':slope,'intercept':intercept,'mean_gap':sum(gaps)/len(gaps),'rank_agreement':agree/total if total else 1.0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output', required=True)
    args=ap.parse_args(); pairs=json.load(open(args.input)); json.dump({'schema_version':1,'analysis':analyze_pairs(pairs)}, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
