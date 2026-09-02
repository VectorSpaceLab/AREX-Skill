
from recovery_utils import accuracy, mechanism_summary

def test_accuracy_and_mechanism_summary():
    assert accuracy(['a','b','a'], ['a','a','a']) == 2/3
    m=mechanism_summary(frozen_model_used=True, universal_prompt_shared=True, prompt_parameters_updated=True, output_transformation_cross_checked=True, optimizer_step_executed=True)
    assert m['all_core_checks_passed']
