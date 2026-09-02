import random

def apply_conditioning_dropout(labels, p_uncond, seed=0, null_token="null"):
    if not 0 <= p_uncond <= 1:
        raise ValueError("p_uncond must be in [0,1]")
    rng=random.Random(seed); out=[]; nulls=0
    for y in labels:
        if rng.random() < p_uncond:
            out.append(null_token); nulls += 1
        else:
            out.append(y)
    return {"conditions":out,"null_count":nulls,"conditional_count":len(labels)-nulls,"p_uncond":p_uncond,"seed":seed}

def tiny_loss_update(params, target_cond, target_uncond, lr=0.1):
    before=dict(params)
    loss_before=(params['cond']-target_cond)**2+(params['uncond']-target_uncond)**2
    params=dict(params)
    params['cond'] -= lr*2*(params['cond']-target_cond)
    params['uncond'] -= lr*2*(params['uncond']-target_uncond)
    loss_after=(params['cond']-target_cond)**2+(params['uncond']-target_uncond)**2
    return {"params_before":before,"params_after":params,"loss_before":loss_before,"loss_after":loss_after}
