import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from evaluator import evaluate

def test_loss_delta_and_mechanism_checks():
    result=evaluate([{"task_id":"new_direct","answer":"yes","format_mode":"direct"},{"task_id":"new_cot","answer":"2","format_mode":"cot"}], ["no","2"], ["yes","2"], {"retained_task_ids":["train"]}, {"loss_before":0.8,"loss_after":0.5,"optimizer_step_executed":True,"reduced_training_executed":True,"full_model_training_executed":False}, {"metric":"loss_delta","proxy":True})
    assert result["accuracy_delta"] == 0.5
    assert round(result["loss_delta"], 6) == 0.3
    assert result["mechanism_checks"]["target_metric_match"] is True
    assert result["mechanism_checks"]["loss_decreased"] is True
    assert result["mechanism_checks"]["cot_coverage_present"] is True
if __name__ == "__main__": test_loss_delta_and_mechanism_checks()
