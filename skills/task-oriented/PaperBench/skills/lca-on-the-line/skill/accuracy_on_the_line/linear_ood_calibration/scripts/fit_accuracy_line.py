#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def fit_accuracy_line(records):
    if isinstance(records, dict): records=records.get('records', [])
    if len(records) < 2: raise ValueError('at least two records are required')
    xs=[float(r['id_accuracy']) for r in records]; ys=[float(r['ood_accuracy']) for r in records]
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    varx=sum((x-mx)**2 for x in xs)
    vary=sum((y-my)**2 for y in ys)
    if varx == 0 or vary == 0: raise ValueError('nonzero variance is required')
    cov=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    slope=cov/varx; intercept=my-slope*mx
    pearson=cov/math.sqrt(varx*vary)
    preds=[]; abs_res=[]
    for r,x,y in zip(records,xs,ys):
        pred=slope*x+intercept; residual=y-pred; abs_res.append(abs(residual))
        preds.append({'model_id':r['model_id'],'id_accuracy':x,'ood_accuracy':y,'predicted_ood_accuracy':pred,'residual':residual})
    return {'slope':slope,'intercept':intercept,'pearson_r':pearson,'mean_absolute_residual':sum(abs_res)/n,'predictions':preds,'count':n}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--output', default='')
    args=ap.parse_args(); data=json.loads(Path(args.input).read_text()); result=fit_accuracy_line(data)
    text=json.dumps(result, indent=2)
    if args.output: Path(args.output).write_text(text + chr(10))
    print(text)
if __name__ == '__main__': main()
