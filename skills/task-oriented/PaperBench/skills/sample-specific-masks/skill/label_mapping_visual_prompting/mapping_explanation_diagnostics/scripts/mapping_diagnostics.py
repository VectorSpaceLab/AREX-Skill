from __future__ import annotations

def mapping_stability(history):
    if len(history)<2: return 1.0
    scores=[]
    for a,b in zip(history, history[1:]):
        keys=set(a)|set(b); scores.append(sum(a.get(k)==b.get(k) for k in keys)/len(keys))
    return sum(scores)/len(scores)

def explain_mapping(mapping, target_desc=None, source_desc=None):
    target_desc=target_desc or {}; source_desc=source_desc or {}; rows=[]
    for t,s in mapping.items():
        shared=sorted(set(target_desc.get(t,[])) & set(source_desc.get(s,[])))
        rows.append({'target':t,'source':s,'shared_attributes':shared,'explanation': (f'{t} and {s} share '+', '.join(shared)) if shared else 'no descriptor overlap available'})
    return rows

def diagnose(history, target_desc=None, source_desc=None, metrics=None):
    if not history: raise ValueError('history is empty')
    initial,final=history[0],history[-1]
    changed=[k for k in initial if initial.get(k)!=final.get(k)]
    return {'changed_count':len(changed),'changed_targets':changed,'stability':mapping_stability(history),'explanations':explain_mapping(final,target_desc,source_desc),'metrics':metrics or {}}
