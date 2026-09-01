import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from training_loop import train

def test_training_changes_params_and_logs_loss():
    trace=train([{"prompt":"Instruction: answer yes","completion":"yes"},{"prompt":"Instruction: answer no not","completion":"no"}], learning_rate=0.2, steps=2)
    assert trace["optimizer_step_executed"] is True
    assert trace["params_before"] != trace["params_after"]
    assert isinstance(trace["loss_before"], float)
if __name__ == "__main__": test_training_changes_params_and_logs_loss()
