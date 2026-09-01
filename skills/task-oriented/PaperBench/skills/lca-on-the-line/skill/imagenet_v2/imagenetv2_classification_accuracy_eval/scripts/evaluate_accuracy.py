#!/usr/bin/env python3
import argparse, json

def _sampled(payload):
    if isinstance(payload, dict): return payload.get('sampled', payload.get('records', []))
    return payload

def compute_accuracy(records, original_top1=None, original_top5=None):
    if not records: raise ValueError('no records')
    top1=top5=0
    for r in records:
        label=str(r['label']); preds=[str(p) for p in r['predictions']]
        top1 += bool(preds and preds[0] == label)
        top5 += label in preds[:5]
    n=len(records); metrics={'sample_count':n,'top1':top1/n,'top5':top5/n}
    if original_top1 is not None: metrics['top1_drop']=float(original_top1)-metrics['top1']
    if original_top5 is not None: metrics['top5_drop']=float(original_top5)-metrics['top5']
    return metrics

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--original-top1', type=float); ap.add_argument('--original-top5', type=float); ap.add_argument('--output', required=True)
    args=ap.parse_args(); payload=json.load(open(args.input)); metrics=compute_accuracy(_sampled(payload), args.original_top1, args.original_top5); json.dump({'schema_version':1,'metrics':metrics}, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
