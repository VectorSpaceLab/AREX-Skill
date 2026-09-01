
from __future__ import annotations

def effective_units(layer_mask, head_mask, intermediate_mask, hidden_mask=None):
    """Compose CoFi-style coarse and fine masks.

    layer_mask: list of per-layer keep values. 0 disables all units in that layer.
    head_mask/intermediate_mask: nested lists indexed by layer.
    hidden_mask: optional global hidden-dimension mask.
    """
    eff_heads=[]; eff_inter=[]
    for i, lm in enumerate(layer_mask):
        eff_heads.append([float(lm)*float(v) for v in head_mask[i]])
        eff_inter.append([float(lm)*float(v) for v in intermediate_mask[i]])
    hidden=[float(v) for v in (hidden_mask or [])]
    return {"heads":eff_heads,"intermediate":eff_inter,"hidden":hidden}

def estimate_active_parameters(effective, head_size=4, intermediate_size_per_dim=2, hidden_size_per_dim=1):
    heads=sum(sum(row) for row in effective.get('heads',[]))*head_size
    inter=sum(sum(row) for row in effective.get('intermediate',[]))*intermediate_size_per_dim
    hidden=sum(effective.get('hidden',[]))*hidden_size_per_dim
    total=heads+inter+hidden
    return {"active_parameters": total, "active_heads": sum(sum(row) for row in effective.get('heads',[])), "active_intermediate_dims": sum(sum(row) for row in effective.get('intermediate',[]))}

def summarize_pruned_structure(layer_mask, head_mask, intermediate_mask, hidden_mask=None):
    eff=effective_units(layer_mask, head_mask, intermediate_mask, hidden_mask)
    return {"effective": eff, "parameter_estimate": estimate_active_parameters(eff)}
