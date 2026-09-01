from __future__ import annotations
from collections import Counter

def top1_from_logits(logits):
    return [max(range(len(row)), key=lambda i: row[i]) for row in logits]

def compute_frequency_mapping(grouped_predictions, target_labels=None, source_labels=None):
    if target_labels is None: target_labels=list(grouped_predictions.keys())
    all_preds=[p for t in target_labels for p in grouped_predictions[t]]
    if source_labels is None: source_labels=sorted(set(all_preds))
    order={s:i for i,s in enumerate(source_labels)}
    used=set(); mapping={}; freqs={}; audit=[]
    for t in target_labels:
        preds=list(grouped_predictions.get(t, []))
        if not preds: raise ValueError(f'empty target class: {t}')
        c=Counter(preds); freqs[t]=dict(c)
        candidates=sorted(c, key=lambda s:(-c[s], order.get(s, 10**9), str(s)))
        chosen=None; duplicate=False
        for s in candidates:
            if s not in used:
                chosen=s; break
        if chosen is None:
            chosen=candidates[0]; duplicate=True
        mapping[t]=chosen; used.add(chosen)
        audit.append({'target':t,'chosen_source':chosen,'counts':dict(c),'duplicate_assignment':duplicate})
    return {'mapping':mapping,'frequencies':freqs,'audit':audit}
