
def hit_rate(rows):
    hits=0
    for r in rows:
        toks=[t.lower() for t in r['tokens']]
        targets=[t.lower() for t in r['target_words']]
        hits += int(any(t in toks for t in targets))
    return hits/len(rows) if rows else 0.0

def mechanism_ok(checks):
    required=['attribute_model_used','latent_perturbation_executed','kl_regularization_used','candidate_reranking_executed','base_model_frozen']
    return all(bool(checks.get(k)) for k in required)
