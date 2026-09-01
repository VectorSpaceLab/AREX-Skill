def guided_score(cond, uncond, w):
    if isinstance(cond,(int,float)) and isinstance(uncond,(int,float)):
        return (1+w)*cond - w*uncond
    if len(cond) != len(uncond):
        raise ValueError('conditional and unconditional predictions must have the same length')
    return [(1+w)*c - w*u for c,u in zip(cond,uncond)]

def guidance_audit(cond, uncond, w):
    return {'formula':'(1+w)*conditional - w*unconditional','w':w,'guided':guided_score(cond,uncond,w)}
