def evaluate_topic_proxy(tokens, target_words, decoder_trace=None, training_trace=None, prefix_examples=None):
    toks=list(tokens); targets=set(target_words)
    hits=[t for t in toks if t in targets]
    rate=len(hits)/len(toks) if toks else 0.0
    coverage=len(set(hits))/len(targets) if targets else 0.0
    distinct=len(set(toks))/len(toks) if toks else 0.0
    trace=decoder_trace or {}
    probs=[v.get('probability') for v in trace.values() if isinstance(v, dict)]
    checks={
        'prefix_labels_built': bool(prefix_examples),
        'future_probabilities_used': any('future_probability' in v for v in trace.values() if isinstance(v, dict)),
        'adjusted_logits_computed': any('adjusted_logit' in v for v in trace.values() if isinstance(v, dict)),
        'renormalized_distribution': bool(probs) and abs(sum(probs)-1.0) < 1e-6,
        'optimizer_step_executed': False,
        'parameters_changed': False,
    }
    if training_trace:
        before=training_trace.get('params_before')
        after=training_trace.get('params_after')
        checks['optimizer_step_executed']=bool(training_trace.get('optimizer_step_executed'))
        checks['parameters_changed']=before != after
        checks['loss_decreased']=training_trace.get('loss_after', 1e9) <= training_trace.get('loss_before', -1e9)
    return {'metrics': {'topic_token_rate': rate, 'topic_word_coverage': coverage, 'distinct_1': distinct}, 'mechanism_checks': checks}
