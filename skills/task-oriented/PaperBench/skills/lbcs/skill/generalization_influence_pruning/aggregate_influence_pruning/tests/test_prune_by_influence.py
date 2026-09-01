import importlib.util, pathlib
path=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'prune_by_influence.py'
spec=importlib.util.spec_from_file_location('prune', path); prune=importlib.util.module_from_spec(spec); spec.loader.exec_module(prune)
res=prune.select_subset([[1,0],[-1,0],[0,0.8]], epsilon=0.1)
assert res['selected_count']==2
assert res['selected_indices']==[0,1]
assert res['feasible'] is True
