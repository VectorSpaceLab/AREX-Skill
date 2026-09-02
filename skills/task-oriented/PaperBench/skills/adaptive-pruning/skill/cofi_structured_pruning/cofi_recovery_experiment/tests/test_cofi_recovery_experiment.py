
import tempfile, sys, pathlib
# Paths are injected by validation command in this attempt.
def test_proxy_runs_and_changes_params():
    from run_cofi_proxy import run_proxy
    with tempfile.TemporaryDirectory() as d:
        result=run_proxy(d)
        assert result['metric'] > 0
        checks=result['mechanism_checks']
        assert checks['multi_granularity_masks_executed']
        assert checks['layerwise_distillation_executed']
        assert checks['optimizer_step_executed']
