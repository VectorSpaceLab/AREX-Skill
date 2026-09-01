import argparse, json

def wanda_scores(weights, activation_norms):
    if not weights or not weights[0]: raise ValueError('empty weights')
    width=len(weights[0])
    if len(activation_norms)!=width: raise ValueError('activation norm length mismatch')
    if any(len(r)!=width for r in weights): raise ValueError('ragged weights')
    return [[abs(float(v))*float(activation_norms[j]) for j,v in enumerate(row)] for row in weights]

def row_prune_mask(scores, sparsity_ratio):
    if not (0 <= sparsity_ratio < 1): raise ValueError('sparsity_ratio must be in [0,1)')
    width=len(scores[0]); k=int(width*sparsity_ratio); masks=[]
    for row in scores:
        idx=sorted(range(width), key=lambda j:(row[j], j))[:k]
        s=set(idx); masks.append([j in s for j in range(width)])
    return masks

def apply_mask(weights, mask):
    return [[0.0 if mask[i][j] else float(weights[i][j]) for j in range(len(weights[i]))] for i in range(len(weights))]

def wanda_prune(weights, activation_norms, sparsity_ratio):
    scores=wanda_scores(weights, activation_norms); mask=row_prune_mask(scores, sparsity_ratio); pruned=apply_mask(weights, mask)
    removed=sum(x for r in mask for x in r); total=sum(len(r) for r in mask)
    return {'scores':scores,'mask':mask,'pruned_weights':pruned,'metadata':{'removed':removed,'total':total,'sparsity':removed/total}}

def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output', required=True); p.add_argument('--sparsity-ratio', type=float, default=0.5)
    a=p.parse_args(); d=json.load(open(a.input)); json.dump(wanda_prune(d['weights'], d['activation_norms'], a.sparsity_ratio), open(a.output,'w'), indent=2)
if __name__=='__main__': main()
