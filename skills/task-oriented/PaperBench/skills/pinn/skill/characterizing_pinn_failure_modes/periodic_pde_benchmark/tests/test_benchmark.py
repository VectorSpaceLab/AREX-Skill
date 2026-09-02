from benchmark import build_convection_benchmark


def test_convection_benchmark_shapes_and_periodicity():
    bench = build_convection_benchmark(beta=3.0, x_points=8, t_points=4, collocation_count=5, seed=1)
    assert bench["system"] == "convection"
    assert len(bench["grid"]["values"]) == 4
    assert len(bench["grid"]["values"][0]) == 8
    assert len(bench["collocation"]) == 5
    for left, right in bench["boundary_pairs"]:
        assert left[1] == right[1]
    assert bench["grid"]["values"][0] != bench["grid"]["values"][-1]
