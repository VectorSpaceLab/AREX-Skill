def alignment_distance(source_reps, target_reps):
    if not source_reps or not target_reps: return None
    m1=[sum(col)/len(source_reps) for col in zip(*source_reps)]
    m2=[sum(col)/len(target_reps) for col in zip(*target_reps)]
    return sum(abs(a-b) for a,b in zip(m1,m2))

def check(trace, threshold=0.5):
    return {'source_model_frozen': trace.get('source_unchanged') is True, 'reprogramming_parameters_updated': trace.get('params_before') != trace.get('params_after'), 'target_loss_decreased': trace.get('loss_after', 9e9) < trace.get('loss_before', -9e9), 'numeric_metric_present': isinstance(trace.get('accuracy_after'), (int,float)), 'proxy_threshold_met': trace.get('accuracy_after',0) >= threshold}
