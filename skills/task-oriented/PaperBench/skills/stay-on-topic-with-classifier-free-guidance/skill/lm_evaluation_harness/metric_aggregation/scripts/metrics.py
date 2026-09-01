import re
from collections import Counter

def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',str(s).lower()).split())
def accuracy(preds, golds): return sum(str(p)==str(g) for p,g in zip(preds,golds))/len(golds) if golds else 0.0
def exact_match(preds,golds): return sum(norm(p)==norm(g) for p,g in zip(preds,golds))/len(golds) if golds else 0.0
def token_f1_one(p,g):
    pt=norm(p).split(); gt=norm(g).split()
    if not pt or not gt: return 1.0 if pt==gt else 0.0
    common=sum((Counter(pt)&Counter(gt)).values())
    if common==0: return 0.0
    prec=common/len(pt); rec=common/len(gt); return 2*prec*rec/(prec+rec)
def token_f1(preds,golds): return sum(token_f1_one(p,g) for p,g in zip(preds,golds))/len(golds) if golds else 0.0
def compute_metrics(preds,golds,metrics):
    out={};
    for m in metrics:
        out[m]={'accuracy':accuracy,'exact_match':exact_match,'f1':token_f1}[m](preds,golds)
    return out
