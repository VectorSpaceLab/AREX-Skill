
from __future__ import annotations

def monotone_alignment(num_teacher_layers, student_survival_mask):
    surviving=[i for i,v in enumerate(student_survival_mask) if v]
    if not surviving:
        return []
    if len(surviving)==1:
        return [(surviving[0], num_teacher_layers-1)]
    pairs=[]
    for rank, student_idx in enumerate(surviving):
        teacher_idx=round(rank*(num_teacher_layers-1)/(len(surviving)-1))
        pairs.append((student_idx, int(teacher_idx)))
    return pairs

def _flatten(v):
    out=[]
    for item in v:
        if isinstance(item, (list, tuple)):
            out.extend(_flatten(item))
        else:
            out.append(float(item))
    return out

def mse(a,b):
    aa=_flatten(a); bb=_flatten(b)
    if len(aa)!=len(bb):
        raise ValueError('vectors must have same length')
    return sum((float(x)-float(y))**2 for x,y in zip(aa,bb))/max(1,len(aa))

def layerwise_distillation_loss(teacher_states, student_states, student_survival_mask):
    pairs=monotone_alignment(len(teacher_states), student_survival_mask)
    if not pairs:
        return {"alignment": [], "loss": None, "valid": False}
    losses=[]
    for s,t in pairs:
        losses.append(mse(student_states[s], teacher_states[t]))
    return {"alignment": pairs, "loss": sum(losses)/len(losses), "valid": True}
