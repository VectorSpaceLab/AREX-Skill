import argparse, json, math, sys
from pathlib import Path
try:
    from cdc_loss import cdc_loss
except Exception:
    pass

def transform(source, params):
    return [[params['scale']*x + params['bias'] for x in row] for row in source]

def mse(a,b): return sum((x-y)**2 for x,y in zip(a,b))/len(a)
def nearest_mse(v, anchors): return min(mse(v,a) for a in anchors)

def total_loss(source, params, anchors, routes, weights):
    adapted=transform(source, params)
    cdc=cdc_loss({'proxy': source}, {'proxy': adapted})['total_loss']
    image_items=[adapted[r['index']] for r in routes if r['route']=='image']
    patch_items=[adapted[r['index']] for r in routes if r['route']=='patch']
    image=sum(nearest_mse(v, anchors) for v in image_items)/len(image_items) if image_items else 0.0
    patch=sum(sum(abs(x) for x in v)/len(v) for v in patch_items)/len(patch_items) if patch_items else 0.0
    total=weights.get('cdc',1.0)*cdc + weights.get('image',1.0)*image + weights.get('patch',0.1)*patch
    return {'total': total, 'cdc': cdc, 'image': image, 'patch': patch, 'adapted': adapted}

def finite_difference_step(source, params, anchors, routes, weights, lr=0.2, eps=1e-4):
    before=dict(params); loss_before=total_loss(source, before, anchors, routes, weights)
    grads={}
    for key in ['scale','bias']:
        plus=dict(before); minus=dict(before); plus[key]+=eps; minus[key]-=eps
        grads[key]=(total_loss(source, plus, anchors, routes, weights)['total']-total_loss(source, minus, anchors, routes, weights)['total'])/(2*eps)
    after={k: before[k]-lr*grads[k] for k in before}
    loss_after=total_loss(source, after, anchors, routes, weights)
    return {'loss_before': loss_before['total'], 'loss_after': loss_after['total'], 'components_before': loss_before, 'components_after': loss_after, 'params_before': before, 'params_after': after, 'gradients': grads, 'optimizer_state_changed': before != after}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--output', required=True)
    args=ap.parse_args(); data=json.load(open(args.input))
    out=finite_difference_step(data['source'], data['params'], data['anchors'], data['routes'], data.get('weights',{}), data.get('lr',0.2))
    json.dump(out, open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
