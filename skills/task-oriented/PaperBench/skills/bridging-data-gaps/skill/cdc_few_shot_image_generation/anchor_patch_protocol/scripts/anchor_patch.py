import argparse, json, math

def distance(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

def route_latents(latents, anchors, threshold):
    if threshold < 0: raise ValueError('threshold must be non-negative')
    if not anchors: raise ValueError('at least one anchor is required')
    dim=len(anchors[0])
    if any(len(v)!=dim for v in anchors+latents): raise ValueError('all vectors must share dimensionality')
    routes=[]
    for idx, z in enumerate(latents):
        distances=[distance(z,a) for a in anchors]
        nearest=min(range(len(distances)), key=lambda i: distances[i])
        label='image' if distances[nearest] <= threshold else 'patch'
        routes.append({'index': idx, 'route': label, 'nearest_anchor': nearest, 'distance': distances[nearest]})
    return {'routes': routes, 'counts': {'image': sum(r['route']=='image' for r in routes), 'patch': sum(r['route']=='patch' for r in routes)}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--output', required=True); ap.add_argument('--threshold', type=float, required=True)
    args=ap.parse_args(); data=json.load(open(args.input)); out=route_latents(data['latents'], data['anchors'], args.threshold); json.dump(out, open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
