import argparse, json, math

def _rows(batches):
    if not batches: return []
    if isinstance(batches[0][0], (int,float)):
        return batches
    rows=[]
    for b in batches: rows.extend(b)
    return rows

def activation_norms(batches, norm='l2'):
    rows=_rows(batches)
    if not rows: raise ValueError('no calibration rows')
    width=len(rows[0])
    if any(len(r)!=width for r in rows): raise ValueError('ragged calibration rows')
    vals=[]
    for j in range(width):
        col=[float(r[j]) for r in rows]
        if norm=='l2': vals.append(math.sqrt(sum(x*x for x in col)))
        elif norm=='l1': vals.append(sum(abs(x) for x in col))
        elif norm=='linf': vals.append(max(abs(x) for x in col))
        else: raise ValueError('unsupported norm')
    order=sorted(range(width), key=lambda i: vals[i], reverse=True)
    return {'activation_norms': vals, 'metadata': {'norm': norm, 'rows': len(rows), 'channels': width, 'descending_channels': order}}

def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output', required=True); p.add_argument('--norm', default='l2')
    a=p.parse_args(); data=json.load(open(a.input)); res=activation_norms(data.get('batches', data), a.norm); json.dump(res, open(a.output,'w'), indent=2)
if __name__=='__main__': main()
