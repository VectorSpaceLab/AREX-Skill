from estimators import power_iteration, hutchinson_trace

def test_estimators_on_diagonal_hessian():
    def hvp(v): return [4.0*v[0], 2.0*v[1]]
    eig = power_iteration(hvp, 2, max_iter=30, initial=[1.0, 0.5])
    assert abs(eig['eigenvalue'] - 4.0) < 1e-5
    trace = hutchinson_trace(hvp, 2, probes=[[1.0, 1.0], [1.0, -1.0]])
    assert trace['trace_estimate'] == 6.0

from estimators import estimator_contract

def test_estimator_contract_metadata():
    contract = estimator_contract()
    assert contract['requires_hvp'] is True
    assert contract['outputs_numeric_trace'] is True
