import importlib.util, pathlib
path=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'check_gap_bound.py'
spec=importlib.util.spec_from_file_location('gap', path); gap=importlib.util.module_from_spec(spec); spec.loader.exec_module(gap)
t={'dataset':'d','split':'s','metric':'m','paper_value':0.1}
res=gap.check_gap(t,0.1,0.2,0.9,0.8,{'influence_vectors_computed':True,'aggregate_optimizer_executed':True,'metric_gap_computed':True},t)
assert res['ok'] is True
assert abs(res['observed_metric_gap']-0.1)<1e-9
fail=gap.check_gap(t,0.3,0.2,0.9,0.8,{'influence_vectors_computed':True,'aggregate_optimizer_executed':True,'metric_gap_computed':True},t)
assert fail['ok'] is False
