import argparse, json, math


def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(max(dot(a,a), 1e-12))
def cosine(a,b): return dot(a,b)/(norm(a)*norm(b))

def softmax(values, temperature=1.0):
    if temperature <= 0: raise ValueError('temperature must be positive')
    scaled=[v/temperature for v in values]
    m=max(scaled)
    exps=[math.exp(v-m) for v in scaled]
    total=sum(exps)
    return [v/total for v in exps]

def row_distributions(vectors, temperature=1.0):
    if len(vectors) < 2: raise ValueError('at least two vectors are required')
    rows=[]
    for i, anchor in enumerate(vectors):
        sims=[cosine(anchor, other) for j, other in enumerate(vectors) if j != i]
        rows.append({'anchor': i, 'similarities': sims, 'probabilities': softmax(sims, temperature)})
    return rows

def kl(p,q,eps=1e-9):
    return sum(max(pi,eps)*math.log(max(pi,eps)/max(qi,eps)) for pi,qi in zip(p,q))

def cdc_loss(source_layers, adapted_layers, temperature=1.0, eps=1e-9):
    if set(source_layers) != set(adapted_layers): raise ValueError('layer keys must match')
    layer_results={}; all_losses=[]
    for layer in sorted(source_layers):
        src=source_layers[layer]; adp=adapted_layers[layer]
        if len(src) != len(adp): raise ValueError(f'layer {layer} batch sizes differ')
        src_rows=row_distributions(src, temperature); adp_rows=row_distributions(adp, temperature)
        losses=[kl(s['probabilities'], a['probabilities'], eps) for s,a in zip(src_rows, adp_rows)]
        layer_results[layer]={'loss': sum(losses)/len(losses), 'row_losses': losses, 'source_rows': src_rows, 'adapted_rows': adp_rows}
        all_losses.extend(losses)
    return {'total_loss': sum(all_losses)/len(all_losses), 'layers': layer_results}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True); ap.add_argument('--output', required=True); ap.add_argument('--temperature', type=float, default=1.0)
    args=ap.parse_args(); data=json.load(open(args.input))
    out=cdc_loss(data['source_layers'], data['adapted_layers'], args.temperature)
    json.dump(out, open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
