def estimate_linear_importance(weights, samples):
    samples=[list(s) for s in samples]
    if not samples: raise ValueError('at least one unlabeled sample is required')
    totals=[0.0 for _ in weights]
    for sample in samples:
        if len(sample)!=len(weights): raise ValueError('sample dimension must match weights')
        out=sum(w*x for w,x in zip(weights,sample))
        for i,x in enumerate(sample): totals[i]+=abs(2.0*out*x)
    imp=[v/len(samples) for v in totals]
    return {'importance':imp,'sample_count':len(samples),'scalar':'squared_l2_output_norm','labels_used':False,'nonnegative':all(v>=0 for v in imp)}
