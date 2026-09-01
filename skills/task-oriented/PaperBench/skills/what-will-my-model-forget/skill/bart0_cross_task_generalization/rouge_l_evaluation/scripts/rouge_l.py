from __future__ import annotations
import argparse, json, re

def toks(s): return re.findall(r"[A-Za-z0-9]+", str(s).lower())
def lcs(a,b):
    dp=[0]*(len(b)+1)
    for x in a:
        prev=0
        for j,y in enumerate(b,1):
            cur=dp[j]
            dp[j]=prev+1 if x==y else max(dp[j], dp[j-1])
            prev=cur
    return dp[-1]
def rouge_l_f1(pred, ref):
    p=toks(pred); r=toks(ref)
    if not p and not r: return 1.0
    if not p or not r: return 0.0
    m=lcs(p,r); prec=m/len(p); rec=m/len(r)
    return 0.0 if prec+rec==0 else 2*prec*rec/(prec+rec)
def evaluate_pairs(pairs):
    rows=[]
    for pair in pairs:
        score=rouge_l_f1(pair.get('prediction',''), pair.get('reference',''))
        rows.append({**pair, 'rouge_l_f1':score, 'rouge_l_percent':score*100})
    avg=sum(r['rouge_l_percent'] for r in rows)/len(rows) if rows else 0.0
    return {'metric':'rouge_l','score':avg,'examples':rows}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pairs_json'); ap.add_argument('--output',default='')
    ns=ap.parse_args(); out=evaluate_pairs(json.load(open(ns.pairs_json, encoding='utf-8')))
    if ns.output: json.dump(out, open(ns.output,'w',encoding='utf-8'), indent=2)
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
