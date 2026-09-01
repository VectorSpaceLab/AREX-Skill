import argparse, json

def nm_mask(scores, prune_n, prune_m):
    if prune_n <= 0 or prune_m <= 0 or prune_n > prune_m: raise ValueError('need 0 < prune_n <= prune_m')
    if not scores or not scores[0]: raise ValueError('empty scores')
    width=len(scores[0]); masks=[]; groups=width//prune_m
    for row in scores:
        if len(row)!=width: raise ValueError('ragged scores')
        mask=[False]*width
        for g in range(groups):
            start=g*prune_m; inds=list(range(start,start+prune_m))
            chosen=sorted(inds, key=lambda j:(row[j], j))[:prune_n]
            for j in chosen: mask[j]=True
        masks.append(mask)
    removed=sum(x for r in masks for x in r); total=len(scores)*width
    return {'mask':masks,'metadata':{'prune_n':prune_n,'prune_m':prune_m,'complete_groups_per_row':groups,'tail_width':width-groups*prune_m,'removed':removed,'total':total,'sparsity':removed/total}}

def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output', required=True); p.add_argument('--prune-n', type=int, required=True); p.add_argument('--prune-m', type=int, required=True)
    a=p.parse_args(); d=json.load(open(a.input)); json.dump(nm_mask(d['scores'], a.prune_n, a.prune_m), open(a.output,'w'), indent=2)
if __name__=='__main__': main()
