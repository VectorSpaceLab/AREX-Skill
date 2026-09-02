import argparse, json, ast

def _shape(a): return (len(a), len(a[0]) if a else 0)
def _check(ir,vis):
    if _shape(ir)!=_shape(vis): raise ValueError('infrared and visible arrays must have equal shape')
def mean_abs_gradient(x):
    vals=[]
    for i,row in enumerate(x):
        for j,v in enumerate(row):
            if i+1<len(x): vals.append(abs(x[i+1][j]-v))
            if j+1<len(row): vals.append(abs(row[j+1]-v))
    return sum(vals)/len(vals) if vals else 0.0
def fuse_arrays(ir, vis, infrared_weight=0.55, detail_boost=0.10):
    _check(ir,vis)
    base=[]
    for r1,r2 in zip(ir,vis):
        row=[]
        for a,b in zip(r1,r2): row.append(infrared_weight*a+(1-infrared_weight)*b)
        base.append(row)
    vis_mean=sum(sum(r) for r in vis)/(len(vis)*len(vis[0]))
    fused=[]
    for brow,vrow in zip(base,vis):
        fused.append([max(0.0,min(1.0,x+detail_boost*(v-vis_mean))) for x,v in zip(brow,vrow)])
    diag={'infrared_weight':infrared_weight,'detail_boost':detail_boost,'visible_gradient':mean_abs_gradient(vis),'fused_gradient':mean_abs_gradient(fused),'thermal_salience':max(max(r) for r in fused)}
    return fused, diag
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ir',required=True); ap.add_argument('--vis',required=True); ap.add_argument('--output',required=True); ap.add_argument('--weight',type=float,default=0.55)
    ns=ap.parse_args(); ir=ast.literal_eval(ns.ir); vis=ast.literal_eval(ns.vis); fused,diag=fuse_arrays(ir,vis,ns.weight)
    json.dump({'fused':fused,'diagnostics':diag},open(ns.output,'w'),indent=2)
if __name__=='__main__': main()
