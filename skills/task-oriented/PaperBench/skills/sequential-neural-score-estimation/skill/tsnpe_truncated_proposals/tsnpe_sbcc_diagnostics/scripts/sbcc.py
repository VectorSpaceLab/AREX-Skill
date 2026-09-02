import argparse, json

def diagnose(payload):
    true=[float(v) for v in payload['true_log_probs']]; samples=[[float(x) for x in row] for row in payload['posterior_sample_log_probs']]
    thr=float(payload['threshold'])
    if len(true)!=len(samples) or not true: raise ValueError('empty or mismatched coverage inputs')
    cover=[]
    for alpha in [0.5,0.8,0.9,0.95]:
        hits=0
        for t,row in zip(true,samples):
            rank=sum(1 for v in row if v <= t)/len(row)
            if rank >= 1-alpha: hits += 1
        cover.append({'confidence':alpha,'empirical_coverage':hits/len(true)})
    return {'coverage':cover,'ground_truth_in_support_fraction':sum(1 for v in true if v>=thr)/len(true),'mechanism_checks':{'sbcc_coverage_computed':True,'support_inclusion_computed':True}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output', required=True); ns=ap.parse_args(); json.dump(diagnose(json.load(open(ns.input))), open(ns.output,'w'), indent=2)
if __name__=='__main__': main()
