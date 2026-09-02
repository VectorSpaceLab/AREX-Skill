#!/usr/bin/env python3
import argparse,json,math,random,subprocess,sys,time
from pathlib import Path

def w(p,o): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(json.dumps(o,indent=2),encoding='utf-8')
def r(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def se(v,o): return sum((a-b)**2 for a,b in zip(v,o))
def run_chain(output,chains=4,dimension=12,iterations=500,seed=2026,step=0.05,noise=0.08):
    rng=random.Random(seed); opt=[math.sin(i+1)*0.25 for i in range(dimension)]; vecs=[[2.5+0.15*c+rng.uniform(-.25,.25) for _ in range(dimension)] for c in range(chains)]; it=[[list(v)] for v in vecs]; losses=[[] for _ in vecs]
    for _ in range(iterations):
        for c,v in enumerate(vecs):
            nv=[x+step*((opt[i]-x)+rng.gauss(0,noise)) for i,x in enumerate(v)]; vecs[c]=nv; it[c].append(list(nv)); losses[c].append(.5*se(nv,opt))
    last=[sum(v[d] for v in vecs)/chains for d in range(dimension)]
    w(output,{"schema_version":1,"chains":chains,"dimension":dimension,"iterations":iterations,"seed":seed,"objective":"noisy_quadratic_vi_surrogate","optimum":opt,"iterates":it,"loss_trace":losses,"last_estimate":last,"initial_error":se([sum(it[c][0][d] for c in range(chains))/chains for d in range(dimension)],opt),"last_error":se(last,opt)})
def mean(x): return sum(x)/len(x)
def var(x):
    if len(x)<2: return 0.0
    m=mean(x); return sum((a-m)**2 for a in x)/(len(x)-1)
def split_rhat(win):
    sp=[]
    for ch in win:
        h=len(ch)//2; sp += [ch[:h], ch[h:h*2]]
    n=len(sp[0]); dim=len(sp[0][0]); out=[]
    for d in range(dim):
        means=[mean([row[d] for row in ch]) for ch in sp]; vars=[var([row[d] for row in ch]) for ch in sp]; W=mean(vars); B=n*var(means)
        out.append(1.0 if W<=1e-15 and B<=1e-15 else (float('inf') if W<=1e-15 else math.sqrt(max((((n-1)/n)*W+B/n)/W,0))))
    return out
def rhat_file(inp,out,window=100,cutoff=1.1):
    it=r(inp)['iterates']; di=[]
    for end in range(window,len(it[0])+1,window):
        rh=split_rhat([ch[end-window:end] for ch in it]); di.append({"iteration":end-1,"component_rhat":rh,"max_rhat":max(rh)})
        if max(rh)<cutoff: w(out,{"schema_version":1,"converged":True,"start_iteration":end-1,"window_size":window,"cutoff":cutoff,"diagnostics":di}); return
    w(out,{"schema_version":1,"converged":False,"start_iteration":None,"window_size":window,"cutoff":cutoff,"diagnostics":di,"warning":"No rolling window satisfied cutoff."})
def ac(x,lag):
    m=mean(x); den=sum((a-m)**2 for a in x)
    return 0.0 if den<=1e-15 else sum((x[i]-m)*(x[i+lag]-m) for i in range(len(x)-lag))/den
def avg_file(inp,out,start,mcse_tol=.02,ess_thr=20):
    it=r(inp)['iterates']; samples=[]
    for ch in it: samples += ch[start+1:]
    dim=len(samples[0]); avg=[]; ess=[]; mc=[]
    for d in range(dim):
        vals=[s[d] for s in samples]; avg.append(mean(vals)); vv=var(vals); rs=0.0
        for lag in range(1,min(len(vals)//2,200)):
            rho=ac(vals,lag)
            if rho<=0: break
            rs+=rho
        e=max(1,min(len(vals),len(vals)/(1+2*rs))); ess.append(e); mc.append(math.sqrt(vv/e))
    w(out,{"schema_version":1,"start_iteration":start,"sample_count":len(samples),"average_estimate":avg,"component_ess":ess,"component_mcse":mc,"median_mcse":sorted(mc)[len(mc)//2],"min_ess":min(ess),"mcse_tolerance":mcse_tol,"ess_threshold":ess_thr,"stop_passed":sorted(mc)[len(mc)//2]<mcse_tol and min(ess)>ess_thr})
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode'); p.add_argument('--input'); p.add_argument('--output',required=True); p.add_argument('--start-iteration',type=int); p.add_argument('--window-size',type=int,default=100); p.add_argument('--cutoff',type=float,default=1.1); p.add_argument('--iterations',type=int,default=500); a=p.parse_args()
    {'chain':lambda:run_chain(a.output,iterations=a.iterations),'rhat':lambda:rhat_file(a.input,a.output,a.window_size,a.cutoff),'avg':lambda:avg_file(a.input,a.output,a.start_iteration)}[a.mode]()
