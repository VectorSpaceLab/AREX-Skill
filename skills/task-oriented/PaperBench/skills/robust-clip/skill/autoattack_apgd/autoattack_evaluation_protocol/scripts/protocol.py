def predict(logits):
    return max(range(len(logits)), key=lambda i: logits[i])

def evaluate_sequence(logit_fn, examples, labels, attacks):
    clean=[predict(logit_fn(x)) == y for x,y in zip(examples,labels)]
    robust=list(clean); records=[]
    for name, attack in attacks:
        idxs=[i for i,v in enumerate(robust) if v]
        subset=[examples[i] for i in idxs]; sublabels=[labels[i] for i in idxs]
        advs=attack(subset, sublabels) if subset else []
        successes=0
        for local_i, adv in enumerate(advs):
            global_i=idxs[local_i]
            if predict(logit_fn(adv)) != labels[global_i]:
                robust[global_i]=False; successes+=1
        records.append({'attack':name,'evaluated':len(idxs),'successes':successes})
    return {'clean_accuracy':sum(clean)/len(labels), 'robust_accuracy':sum(robust)/len(labels), 'robust_mask':robust, 'per_attack':records}
