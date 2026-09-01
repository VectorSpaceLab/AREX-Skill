from ddpm_protocol import build_protocol, diffuse, reconstruct_x0


def test_reconstructs_clean_when_prediction_matches_noise():
    clean = [[[[1.0, -1.0], [0.5, 0.0]]]]
    noise = [[[[0.2, -0.1], [0.0, 0.3]]]]
    x_t = diffuse(clean, noise, 0.81)
    recovered = reconstruct_x0(x_t, noise, 0.81)
    for row_a, row_b in zip(recovered[0][0], clean[0][0]):
        for got, expected in zip(row_a, row_b):
            assert abs(got - expected) < 1e-9


def test_protocol_uses_shared_noised_batch():
    clean = [[[[1.0, 0.0], [0.0, -1.0]]]]
    noise = [[[[0.1, 0.2], [0.3, 0.4]]]]
    out = build_protocol(clean, noise, noise, [[[[0.0, 0.0], [0.0, 0.0]]]], 0.64)
    assert out["metadata"]["shape"] == [1, 1, 2, 2]
    assert out["source_x0_hat"] != out["adapted_x0_hat"]
