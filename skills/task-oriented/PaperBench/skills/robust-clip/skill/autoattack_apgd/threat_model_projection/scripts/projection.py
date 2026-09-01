import math

def _rows(x):
    return x if x and isinstance(x[0], list) else [x]

def _same_shape(rows, template):
    return rows if template and isinstance(template[0], list) else rows[0]

def project(clean, candidate, norm='Linf', eps=0.3, lower=0.0, upper=1.0):
    clean_rows, cand_rows = _rows(clean), _rows(candidate)
    out=[]; norms=[]; clipped=False
    for c,a in zip(clean_rows,cand_rows):
        delta=[ai-ci for ci,ai in zip(c,a)]
        if norm == 'Linf':
            delta=[max(-eps,min(eps,d)) for d in delta]
        elif norm == 'L2':
            n=math.sqrt(sum(d*d for d in delta))
            if n > eps and n > 0: delta=[d*eps/n for d in delta]
        else:
            raise ValueError('unsupported norm')
        adv=[]
        for ci,d in zip(c,delta):
            val=max(lower,min(upper,ci+d)); clipped = clipped or abs(val-(ci+d))>1e-12; adv.append(val)
        out.append(adv)
        diff=[v-ci for v,ci in zip(adv,c)]
        norms.append(max(abs(d) for d in diff) if norm=='Linf' else math.sqrt(sum(d*d for d in diff)))
    return _same_shape(out, clean), {'norms': norms, 'clipped_to_box': clipped, 'norm': norm, 'eps': eps}
