from collections import Counter, defaultdict

def freq_map(source_preds, target_labels, m=1):
    counts=defaultdict(Counter)
    for s,t in zip(source_preds,target_labels): counts[t][s]+=1
    mapping={}
    for t,c in sorted(counts.items()):
        mapping[t]=[s for s,_ in sorted(c.items(), key=lambda kv:(-kv[1], kv[0]))[:m]]
    return mapping

def map_prediction(source_pred, mapping):
    for t,srcs in mapping.items():
        if source_pred in srcs: return t
    return None

def fully_map(logits, weights, bias):
    return [sum(w*x for w,x in zip(row, logits))+b for row,b in zip(weights,bias)]
