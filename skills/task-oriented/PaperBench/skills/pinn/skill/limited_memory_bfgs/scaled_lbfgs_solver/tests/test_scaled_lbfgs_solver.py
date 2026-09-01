from scaled_lbfgs_solver import minimize

def test_scaled_lbfgs_reduces_quadratic():
    def obj(x): return 0.5*(10*x[0]*x[0] + x[1]*x[1])
    def grad(x): return [10*x[0], x[1]]
    out = minimize(obj, grad, [2.0, 2.0], memory_limit=3, max_iter=8)
    assert out["objective_final"] < obj([2.0, 2.0])
    assert out["gradient_norm_final"] < (10*2.0)**2
    assert out["memory_final_length"] <= 3
