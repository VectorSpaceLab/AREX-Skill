from __future__ import annotations

def remap_scores(scores, mapping, reducer='sum'):
    scores=list(scores); out={}; used=[]
    for label, inds in mapping.items():
        if not inds: raise ValueError('each adversarial label needs at least one target class')
        vals=[]
        for i in inds:
            if i<0 or i>=len(scores): raise ValueError('mapped index out of range')
            vals.append(scores[i]); used.append(i)
        out[str(label)] = sum(vals)/len(vals) if reducer=='mean' else sum(vals)
    pred=sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return {'adversarial_scores': out, 'prediction': pred, 'metadata': {'mapped_indices': used, 'reducer': reducer}}
