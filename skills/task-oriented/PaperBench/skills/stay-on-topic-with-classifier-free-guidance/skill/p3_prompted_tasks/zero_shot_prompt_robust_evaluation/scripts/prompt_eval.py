from collections import defaultdict


def canon(x): return str(x).strip().lower()

def evaluate(records):
    correct=[canon(r['prediction'])==canon(r['target']) for r in records]
    by_t=defaultdict(list); by_ex=defaultdict(list)
    for r,c in zip(records, correct):
        by_t[r['template_id']].append(c); by_ex[r['example_id']].append(canon(r['prediction']))
    per_template={t:sum(v)/len(v) for t,v in by_t.items()}
    consistent=[len(set(v))==1 for v in by_ex.values() if len(v)>1]
    return {'accuracy':sum(correct)/len(correct) if correct else 0.0,'per_template_accuracy':per_template,'prompt_consistency':sum(consistent)/len(consistent) if consistent else 1.0,'count':len(records)}
