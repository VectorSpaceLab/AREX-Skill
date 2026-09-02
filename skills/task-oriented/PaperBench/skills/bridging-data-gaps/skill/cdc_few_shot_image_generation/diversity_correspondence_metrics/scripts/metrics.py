import argparse, json, math

def dist(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(max(dot(a,a), 1e-12))
def cosine(a,b): return dot(a,b)/(norm(a)*norm(b))

def assign_clusters(samples, anchors):
    assignments=[]
    for i,s in enumerate(samples):
        distances=[dist(s,a) for a in anchors]
        k=min(range(len(distances)), key=lambda j: distances[j])
        assignments.append({'index': i, 'cluster': k, 'distance': distances[k]})
    return assignments

def intra_cluster_distance(samples, anchors):
    assignments=assign_clusters(samples, anchors); values=[]; sizes={}
    for k in range(len(anchors)):
        idx=[a['index'] for a in assignments if a['cluster']==k]; sizes[str(k)]=len(idx)
        if len(idx)<2: values.append(0.0); continue
        ds=[dist(samples[i], samples[j]) for n,i in enumerate(idx) for j in idx[n+1:]]
        values.append(sum(ds)/len(ds))
    return {'average_intra_cluster_distance': sum(values)/len(values), 'cluster_values': values, 'cluster_sizes': sizes, 'assignments': assignments}

def pairwise_sims(vectors): return [cosine(vectors[i], vectors[j]) for i in range(len(vectors)) for j in range(i+1, len(vectors))]
def corr(a,b):
    ma=sum(a)/len(a); mb=sum(b)/len(b); va=sum((x-ma)**2 for x in a); vb=sum((x-mb)**2 for x in b)
    if va == 0 or vb == 0: return 0.0
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(va*vb)

def correspondence_correlation(source, adapted): return corr(pairwise_sims(source), pairwise_sims(adapted))

def rank_agreement(source, adapted):
    src=pairwise_sims(source); adp=pairwise_sims(adapted)
    total=0; agree=0
    for i in range(len(src)):
        for j in range(i+1, len(src)):
            src_order=(src[i] > src[j]) - (src[i] < src[j])
            adp_order=(adp[i] > adp[j]) - (adp[i] < adp[j])
            if src_order == 0: continue
            total += 1
            if src_order == adp_order: agree += 1
    return agree/total if total else 1.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--output', required=True)
    args=ap.parse_args(); data=json.load(open(args.input)); out=intra_cluster_distance(data['samples'], data['anchors'])
    if 'source' in data and 'adapted' in data:
        out['similarity_correlation']=correspondence_correlation(data['source'], data['adapted'])
        out['similarity_rank_agreement']=rank_agreement(data['source'], data['adapted'])
    json.dump(out, open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
