import tempfile, json, shutil
from pathlib import Path
from run_reduced_p3o import run

def test_reduced_harness_decreases_loss():
    with tempfile.TemporaryDirectory() as d:
        attempt = Path(d)
        (attempt/'recovery'/'logs').mkdir(parents=True)
        shutil.copyfile(r'/share/project/yuyang/workspace/Paperbench/record/case9/skill_distillation/p3o_policy_on_off/p3o_policy_on_off_attempt_001/module_plan.json', attempt/'module_plan.json')
        out = run(str(attempt), r'/share/project/yuyang/workspace/Paperbench/record/case9/extracted_skills_attempt_001/p3o_policy_on_off')
        assert out['metrics']['loss_reduction'] > 0
        assert out['mechanism_checks']['reduced_training_executed'] is True
