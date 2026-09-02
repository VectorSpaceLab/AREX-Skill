
def distinct_n(tokens, n):
    grams=[tuple(tokens[i:i+n]) for i in range(max(0,len(tokens)-n+1))]
    return 0.0 if not grams else len(set(grams))/len(grams)

def diversity(tokens):
    return {'dist1':distinct_n(tokens,1),'dist2':distinct_n(tokens,2),'dist3':distinct_n(tokens,3)}

def select_candidate(candidates, min_dist1=0.0):
    enriched=[]
    for c in candidates:
        div=diversity(c['tokens']); row=dict(c); row.update(div); enriched.append(row)
    passed=[c for c in enriched if c['dist1']>=min_dist1]
    pool=passed or enriched
    best=max(pool, key=lambda c:c['attribute_score'])
    best['selection_reason']='passed_diversity' if passed else 'fallback_all_failed_diversity'
    return best, enriched
