import argparse, json, ast, math

def flat(x): return [v for row in x for v in row]
def entropy(x,bins=8):
    vals=flat(x); counts=[0]*bins
    for v in vals: counts[min(bins-1,max(0,int(v*bins)))] += 1
    total=len(vals); ent=0.0
    for c in counts:
        if c:
            p=c/total; ent -= p*math.log(p,2)
    return ent
def contrast(x):
    vals=flat(x); m=sum(vals)/len(vals); return sum(abs(v-m) for v in vals)/len(vals)
def edge_strength(x):
    vals=[]
    for i,row in enumerate(x):
        for j,v in enumerate(row):
            if i+1<len(x): vals.append(abs(x[i+1][j]-v))
            if j+1<len(row): vals.append(abs(row[j+1]-v))
    return sum(vals)/len(vals) if vals else 0.0
def fusion_metrics(ir,vis,fused,runs=None):
    target_edge=max(edge_strength(ir), edge_strength(vis), 1e-9)
    score=0.4*entropy(fused)/3.0 + 0.3*edge_strength(fused)/target_edge + 0.3*contrast(fused)/max(contrast(ir),contrast(vis),1e-9)
    out={'entropy':entropy(fused),'contrast':contrast(fused),'edge_preservation':edge_strength(fused)/target_edge,'fusion_proxy_score':score}
    if runs:
        scores=[fusion_metrics(ir,vis,r)['fusion_proxy_score'] for r in runs]
        out['stability']=1.0/(1.0+(max(scores)-min(scores)))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ir',required=True); ap.add_argument('--vis',required=True); ap.add_argument('--fused',required=True); ap.add_argument('--output',required=True)
    ns=ap.parse_args(); res=fusion_metrics(ast.literal_eval(ns.ir),ast.literal_eval(ns.vis),ast.literal_eval(ns.fused)); json.dump(res,open(ns.output,'w'),indent=2)
if __name__=='__main__': main()
