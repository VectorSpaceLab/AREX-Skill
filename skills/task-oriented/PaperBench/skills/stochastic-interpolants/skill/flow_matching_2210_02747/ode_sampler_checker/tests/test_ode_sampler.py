import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('ode', Path(__file__).resolve().parents[1]/'scripts'/'ode_check.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def test_constant_velocity_reaches_endpoint():
    r=m.euler_constant_velocity([1,-1],[2,3],8); assert r['nfe']==8 and m.endpoint_error(r['final'],[3,2])<1e-12
def test_invalid_steps_fail():
    try: m.euler_constant_velocity([0],[1],0)
    except ValueError as e: assert 'positive' in str(e)
    else: raise AssertionError('zero steps should fail')
