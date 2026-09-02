import importlib.util, pathlib
path=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'influence_estimator.py'
spec=importlib.util.spec_from_file_location('inf', path); inf=importlib.util.module_from_spec(spec); spec.loader.exec_module(inf)
res=inf.estimate_influences(features=[[1,0],[0,1]], labels=[1,0], params=[0,0], damping=0.1)
assert res['metadata']['sample_count']==2
assert len(res['influences'])==2 and len(res['influences'][0])==2
assert all(abs(v)<10 for row in res['influences'] for v in row)
