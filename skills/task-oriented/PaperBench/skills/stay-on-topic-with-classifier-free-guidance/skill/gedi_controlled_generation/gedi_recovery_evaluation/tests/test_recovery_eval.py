import json, pathlib, subprocess, sys, tempfile
script = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'validate_mechanism.py'
result = {'mechanism_checks': {k: True for k in ['posterior_computed','weighted_posterior_applied','rho_filter_applied','guided_token_selected','hybrid_loss_computed','optimizer_step_executed','multiclass_true_false_pairs_built','source_boundary_respected']}}
with tempfile.TemporaryDirectory() as d:
    inp = pathlib.Path(d)/'r.json'; out = pathlib.Path(d)/'o.json'
    inp.write_text(json.dumps(result))
    subprocess.check_call([sys.executable, str(script), str(inp), '--output', str(out)])
    data = json.loads(out.read_text())
    assert data['ok'] is True
    assert data['mechanism_pass_rate'] == 1.0
print('gedi_recovery_evaluation tests passed')
