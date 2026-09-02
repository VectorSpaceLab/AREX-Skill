import argparse, json, math

def matmul_x_wt(x, w):
    return [[sum(float(row[j])*float(out[j]) for j in range(len(out))) for out in w] for row in x]

def norm2(mat): return math.sqrt(sum(v*v for r in mat for v in r))
def rel_error(a,b):
    diff=[[a[i][j]-b[i][j] for j in range(len(a[i]))] for i in range(len(a))]
    den=norm2(a); return 0.0 if den==0 else norm2(diff)/den

def evaluate_pruning(original, pruned, eval_activations, mask):
    dense=matmul_x_wt(eval_activations, original); sparse=matmul_x_wt(eval_activations, pruned)
    total=sum(len(r) for r in mask); removed=sum(x for r in mask for x in r)
    unchanged=True; zero=True
    for i,row in enumerate(mask):
        for j,m in enumerate(row):
            if m and float(pruned[i][j])!=0.0: zero=False
            if (not m) and float(pruned[i][j])!=float(original[i][j]): unchanged=False
    return {'sparsity':removed/total,'relative_output_error':rel_error(dense,sparse),'unmasked_weights_unchanged':unchanged,'masked_weights_zero':zero,'removed':removed,'total':total}

def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output', required=True)
    a=p.parse_args(); d=json.load(open(a.input)); json.dump(evaluate_pruning(d['original_weights'], d['pruned_weights'], d['eval_activations'], d['mask']), open(a.output,'w'), indent=2)
if __name__=='__main__': main()
