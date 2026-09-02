from curvature_core import dot, normalize, matrix_hvp, rayleigh

def test_hvp_and_rayleigh_for_quadratic():
    h = [[3.0, 0.0], [0.0, 1.0]]
    assert matrix_hvp(h, [2.0, -1.0]) == [6.0, -1.0]
    assert rayleigh(h, [1.0, 2.0]) == 7.0
    v = normalize([3.0, 4.0])
    assert round(dot(v, v), 7) == 1.0
