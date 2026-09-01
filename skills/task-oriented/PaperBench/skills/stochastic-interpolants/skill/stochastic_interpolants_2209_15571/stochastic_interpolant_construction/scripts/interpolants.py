import math

def trig_interpolant(x0, x1, t):
    if len(x0) != len(x1):
        raise ValueError("x0 and x1 must have the same length")
    a = math.cos(0.5 * math.pi * t)
    b = math.sin(0.5 * math.pi * t)
    return [a * u + b * v for u, v in zip(x0, x1)]

def trig_derivative(x0, x1, t):
    if len(x0) != len(x1):
        raise ValueError("x0 and x1 must have the same length")
    da = -0.5 * math.pi * math.sin(0.5 * math.pi * t)
    db = 0.5 * math.pi * math.cos(0.5 * math.pi * t)
    return [da * u + db * v for u, v in zip(x0, x1)]

def endpoint_errors(x0, x1):
    left = max(abs(a-b) for a,b in zip(trig_interpolant(x0,x1,0.0), x0))
    right = max(abs(a-b) for a,b in zip(trig_interpolant(x0,x1,1.0), x1))
    return {"t0_max_abs_error": left, "t1_max_abs_error": right}
