from langevin_sampler import run_annealed_langevin


def test_langevin_moves_mean_toward_gaussian_target():
    initial = [[0.0] for _ in range(128)]
    target = [2.0]

    def score_fn(samples, level):
        return [[target[0] - row[0]] for row in samples]

    samples, trace = run_annealed_langevin(initial, score_fn, [3, 2, 1], 0.05, 8, seed=5)
    mean_after = sum(row[0] for row in samples) / len(samples)
    assert abs(mean_after - 2.0) < 2.0
    assert trace["level_count"] == 3
    assert trace["steps_per_level"] == 8
