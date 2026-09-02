def accuracy(predictions, labels):
    if not labels:
        return 0.0
    return sum(int(p==y) for p,y in zip(predictions, labels))/len(labels)

def summarize_recovery(baseline_predictions, episodic_predictions, labels, mechanism_checks, paper_target):
    baseline=accuracy(baseline_predictions, labels)
    episodic=accuracy(episodic_predictions, labels)
    required=['memory_write_executed','sparse_replay_executed','knn_retrieval_executed','local_adaptation_executed','base_parameter_reset_confirmed']
    checks_ok=all(bool(mechanism_checks.get(k)) for k in required)
    return {'metric': 'retained_accuracy_gain_over_baseline', 'baseline_accuracy': baseline, 'episodic_accuracy': episodic, 'gain': episodic-baseline, 'checks_ok': checks_ok, 'paper_target': paper_target}
