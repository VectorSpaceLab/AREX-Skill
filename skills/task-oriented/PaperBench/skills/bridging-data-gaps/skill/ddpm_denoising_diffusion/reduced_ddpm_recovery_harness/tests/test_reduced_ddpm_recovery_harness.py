import tempfile, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from run_reduced_recovery import run

def test_harness_writes_loss_reduction():
    root=Path(tempfile.mkdtemp())
    (root/'recovery'/'logs').mkdir(parents=True)
    (root/'module_plan.json').write_text(json.dumps({'fast_recovery_target':{'dataset':'synthetic_tiny_images','split':'deterministic_8_examples','metric':'epsilon_mse_loss_reduction','paper_value':0.0,'proxy':True,'rationale':'test'}}))
    result=run(root)
    assert result['metrics']['epsilon_mse_loss_reduction'] > 0
    assert (root/'recovery'/'logs'/'training_trace.json').exists()
