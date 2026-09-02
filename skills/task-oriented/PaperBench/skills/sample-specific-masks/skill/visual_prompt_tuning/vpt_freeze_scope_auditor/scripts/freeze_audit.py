
def audit(before, after, trainable_prefixes=('prompt','head')):
    changed=[]; trainable=0; total=0; violations=[]
    for name,b in before.items():
        a=after[name]; n=len(b) if isinstance(b,list) else 1; total+=n
        allowed=any(name.startswith(p) for p in trainable_prefixes)
        if allowed: trainable+=n
        if a!=b: changed.append(name)
        if a!=b and not allowed: violations.append(name)
    return {'ok': not violations, 'changed': changed, 'violations': violations, 'trainable_params': trainable, 'total_params': total, 'trainable_ratio': trainable/total if total else 0.0}
