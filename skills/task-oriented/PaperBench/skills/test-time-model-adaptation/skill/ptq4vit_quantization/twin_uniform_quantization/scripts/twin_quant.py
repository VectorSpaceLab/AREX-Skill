def twin_quantize(values, bits=8, kind='softmax', small_scale=None, large_scale=None):
    if bits < 2: raise ValueError('bits must be at least 2')
    levels=2**(bits-1)-1
    if kind not in {'softmax','gelu'}: raise ValueError('kind must be softmax or gelu')
    if kind=='softmax':
        small_scale = small_scale or 1.0/(levels*4)
        large_scale = large_scale or 1.0/levels
        threshold=levels*small_scale
        out=[]; codes=[]; flags=[]
        for v in values:
            if 0 <= v < threshold:
                q=max(0,min(levels,round(v/small_scale))); flags.append(0); codes.append(q); out.append(q*small_scale)
            else:
                q=max(0,min(levels,round(v/large_scale))); flags.append(1); codes.append(q); out.append(q*large_scale)
        return {'values':out,'codes':codes,'range_flags':flags,'scales':{'r1':small_scale,'r2':large_scale},'kind':kind}
    neg=[abs(v) for v in values if v<0]
    pos=[v for v in values if v>=0]
    small_scale = small_scale or ((max(neg) if neg else 1.0)/levels)
    large_scale = large_scale or ((max(pos) if pos else 1.0)/levels)
    out=[]; codes=[]; flags=[]
    for v in values:
        if v < 0:
            q=max(0,min(levels,round(abs(v)/small_scale))); flags.append(0); codes.append(q); out.append(-q*small_scale)
        else:
            q=max(0,min(levels,round(v/large_scale))); flags.append(1); codes.append(q); out.append(q*large_scale)
    return {'values':out,'codes':codes,'range_flags':flags,'scales':{'r1':small_scale,'r2':large_scale},'kind':kind}

def power_of_two_alignment(scales):
    r1=scales['r1']; r2=scales['r2']
    if r1 <= 0 or r2 <= 0: raise ValueError('scales must be positive')
    ratio=r2/r1
    m=round(__import__('math').log(ratio,2))
    return {'m':m,'aligned':abs((2**m)-ratio) < 1e-9,'ratio':ratio}
