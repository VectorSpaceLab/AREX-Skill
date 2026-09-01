from interpolants import trig_interpolant, trig_derivative, endpoint_errors

def test_endpoints_and_derivative_shape():
    x0=[1.0,-2.0]; x1=[3.0,4.0]
    assert trig_interpolant(x0,x1,0.0)==x0
    y=trig_interpolant(x0,x1,1.0)
    assert max(abs(a-b) for a,b in zip(y,x1)) < 1e-12
    assert len(trig_derivative(x0,x1,0.4)) == 2
    assert endpoint_errors(x0,x1)["t1_max_abs_error"] < 1e-12
