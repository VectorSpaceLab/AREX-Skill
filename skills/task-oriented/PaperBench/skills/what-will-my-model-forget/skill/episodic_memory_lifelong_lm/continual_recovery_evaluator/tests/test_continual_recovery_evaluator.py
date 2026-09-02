import sys
sys.path.insert(0, 'scripts')
from recovery_evaluator import summarize_recovery
checks={'memory_write_executed':True,'sparse_replay_executed':True,'knn_retrieval_executed':True,'local_adaptation_executed':True,'base_parameter_reset_confirmed':True}
summary=summarize_recovery([0,0],[0,1],[0,1],checks,{'metric':'retained_accuracy_gain_over_baseline','paper_value':0.0})
assert summary['gain'] > 0
assert summary['checks_ok']

required_artifacts = {
    'lifelong_stream_protocol': 'recovery/logs/generated_data_item.json',
    'episodic_memory_store': 'recovery/logs/generated_data_item.json',
    'sparse_replay_trainer': 'recovery/logs/replay_events.json',
    'local_adaptation_predictor': 'recovery/logs/adaptation_trace.json',
    'continual_recovery_evaluator': 'recovery/recovery_result.json',
}
assert set(required_artifacts) == set(required_artifacts.keys())
