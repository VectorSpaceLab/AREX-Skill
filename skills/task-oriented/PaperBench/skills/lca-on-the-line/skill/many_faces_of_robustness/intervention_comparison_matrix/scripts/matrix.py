def compare(rows, baseline, metric_direction):
    base=next(row for row in rows if row["intervention"]==baseline)
    out=[]
    for row in rows:
        deltas={}
        signs={}
        for key,value in row.items():
            if key=="intervention" or key not in base:
                continue
            delta=(base[key]-value) if metric_direction=="lower_is_better" else (value-base[key])
            deltas[key]=delta
            signs[key]="+" if delta>0 else "-" if delta<0 else "0"
        out.append({"intervention":row["intervention"],"deltas":deltas,"signs":signs})
    return out

def best(rows, dataset, metric_direction):
    reverse=metric_direction=="higher_is_better"
    available=[row for row in rows if dataset in row]
    return sorted(available, key=lambda r:r[dataset], reverse=reverse)[0]["intervention"]
