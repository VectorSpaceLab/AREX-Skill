from proxy_objectives import make_rotated_ellipsoid

def test_rotated_ellipsoid_positive_and_minimum_zero():
    obj, matrix = make_rotated_ellipsoid()
    assert obj([0.0, 0.0]) == 0.0
    assert obj([1.0, 0.0]) > 0.0
    assert len(matrix) == 2 and len(matrix[0]) == 2
