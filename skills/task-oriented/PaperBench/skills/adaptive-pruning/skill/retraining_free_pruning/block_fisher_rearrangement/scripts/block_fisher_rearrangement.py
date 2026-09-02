def objective(mask, block):
    z=[1-int(x) for x in mask]
    return sum(z[i]*float(block[i][j])*z[j] for i in range(len(z)) for j in range(len(z)))

def rearrange_layer(mask, block, max_passes=5):
    m=[int(x) for x in mask]
    n=len(m)
    if any(len(row)!=n for row in block): raise ValueError('block must be square')
    before=objective(m,block); trace=[]
    for _ in range(max_passes):
        improved=False
        pruned=sorted([i for i,v in enumerate(m) if v==0], key=lambda i: -float(block[i][i]))
        kept=[i for i,v in enumerate(m) if v==1]
        for p in pruned:
            current=objective(m,block); best=(current,None)
            for k in kept:
                cand=m[:]; cand[p]=1; cand[k]=0
                val=objective(cand,block)
                if val < best[0]-1e-12: best=(val,k)
            if best[1] is not None:
                k=best[1]; m[p]=1; m[k]=0
                trace.append({'pruned_to_kept':p,'kept_to_pruned':k,'objective':best[0]})
                improved=True
                break
        if not improved: break
    return {'mask':m,'objective_before':before,'objective_after':objective(m,block),'swaps':trace}

def rearrange_layers(masks, blocks, max_passes=5):
    return [rearrange_layer(m,b,max_passes) for m,b in zip(masks,blocks)]
