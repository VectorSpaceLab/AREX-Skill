import re
from collections import Counter

def apply_filter(resps, spec):
    vals=list(resps)
    trace=[]
    for f in spec:
        fn=f['function']
        if fn=='take_first_k': vals=vals[:int(f['k'])]
        elif fn=='regex':
            pat=re.compile(f['regex_pattern']); vals=[(pat.search(str(v)).group(1) if pat.search(str(v)) else '') for v in vals]
        elif fn=='majority_vote':
            vals=[Counter(vals).most_common(1)[0][0] if vals else '']
        elif fn=='take_first': vals=[vals[0] if vals else '']
        else: raise ValueError('unknown filter '+fn)
        trace.append({'function':fn,'values':list(vals)})
    return (vals[0] if len(vals)==1 else vals), trace

def apply_pipeline(grouped, spec):
    preds=[]; traces=[]
    for resps in grouped:
        pred, tr=apply_filter(resps, spec); preds.append(pred); traces.append(tr)
    return preds, traces
