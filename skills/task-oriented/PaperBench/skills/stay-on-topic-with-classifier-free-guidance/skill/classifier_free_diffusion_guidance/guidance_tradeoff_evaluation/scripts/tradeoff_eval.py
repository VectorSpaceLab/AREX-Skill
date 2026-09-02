def mean(xs): return sum(xs)/len(xs)
def variance(xs):
    m=mean(xs); return sum((x-m)**2 for x in xs)/len(xs)
def evaluate_tradeoff(samples_by_w, class_mean):
    rows=[]
    for w in sorted(samples_by_w):
        xs=samples_by_w[w]
        mad=mean([abs(x-class_mean) for x in xs])
        confidence=1.0/(1.0+mad)
        rows.append({'w':w,'confidence':confidence,'diversity':variance(xs)})
    low, high=rows[0], rows[-1]
    confidence_increased=high['confidence']>low['confidence']
    diversity_decreased=high['diversity']<low['diversity']
    score=(1 if confidence_increased else 0)+(1 if diversity_decreased else 0)
    return {'per_w':rows,'confidence_increased':confidence_increased,'diversity_decreased':diversity_decreased,'guidance_tradeoff_score':score/2}
