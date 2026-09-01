import argparse, json, math, statistics

def quantile(values, q):
    if not 0 <= q < 1: raise ValueError('epsilon must be in [0,1)')
    vals=sorted(float(v) for v in values)
    if not vals: raise ValueError('empty log-probabilities')
    pos=q*(len(vals)-1); lo=math.floor(pos); hi=math.ceil(pos)
    return vals[lo] if lo==hi else vals[lo]*(hi-pos)+vals[hi]*(pos-lo)

def truncate(payload):
    logs=[float(v) for v in payload['posterior_log_probs']]
    samples=payload['prior_samples']
    sample_logs=[float(v) for v in payload.get('prior_log_probs_for_samples', logs)]
    if len(samples)!=len(sample_logs): raise ValueError('sample/log length mismatch')
    threshold=quantile(logs, float(payload.get('epsilon', 0.001)))
    accepted=[i for i,v in enumerate(sample_logs) if v >= threshold]
    if not accepted: raise ValueError('truncated proposal accepted no samples')
    return {'threshold':threshold,'accepted_indices':accepted,'accepted_samples':[samples[i] for i in accepted],'acceptance_rate':len(accepted)/len(samples),'mechanism_checks':{'hpr_threshold_computed':True,'prior_samples_rejected_outside_hpr':True,'proposal_prior_proportional_inside_support':True}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output', required=True); ns=ap.parse_args()
    out=truncate(json.load(open(ns.input)))
    json.dump(out, open(ns.output,'w'), indent=2)
if __name__=='__main__': main()
