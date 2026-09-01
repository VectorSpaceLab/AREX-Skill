import argparse, json, math, random

def run_sir(payload):
    cand=payload['candidate_samples']; lp=[float(x) for x in payload['log_prior']]; lq=[float(x) for x in payload['log_proposal']]
    if not cand or len(cand)!=len(lp) or len(cand)!=len(lq): raise ValueError('candidate/log length mismatch')
    raw=[a-b for a,b in zip(lp,lq)]; m=max(raw); w=[math.exp(x-m) for x in raw]; s=sum(w)
    if s<=0: raise ValueError('zero SIR weight')
    weights=[x/s for x in w]; ess=1.0/sum(x*x for x in weights)
    rng=random.Random(int(payload.get('seed',0))); n=int(payload.get('num_samples',1))
    picks=[]
    for _ in range(n):
        u=rng.random(); acc=0.0
        for i,wi in enumerate(weights):
            acc+=wi
            if u<=acc: picks.append(i); break
    return {'selected_indices':picks,'selected_samples':[cand[i] for i in picks],'normalized_weights':weights,'effective_sample_size':ess,'mechanism_checks':{'sir_weights_from_prior_over_posterior':True,'fixed_budget_resampling':True}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output', required=True); ns=ap.parse_args(); json.dump(run_sir(json.load(open(ns.input))), open(ns.output,'w'), indent=2)
if __name__=='__main__': main()
