from posterior_sampling import sample_posteriors


def task():
    return {'task_name': 'gaussian_linear_proxy', 'posterior': {'mean': [0.0, 1.0], 'variance': 0.25}}


def test_sampling_shapes_are_deterministic():
    a = sample_posteriors(task(), num_samples=8, seed=3)
    b = sample_posteriors(task(), num_samples=8, seed=3)
    assert a['reference_samples'] == b['reference_samples']
    assert len(a['approximate_samples']) == 8
    assert len(a['approximate_samples'][0]) == 2


def test_shifted_mode_changes_approximation_mean():
    out = sample_posteriors(task(), num_samples=8, seed=3, mode='shifted')
    assert out['approximation']['mean'][0] == 0.75


def test_unknown_sampling_mode_rejected():
    try:
        sample_posteriors(task(), num_samples=8, seed=3, mode='bad_mode')
    except ValueError as exc:
        assert 'unknown approximation mode' in str(exc)
    else:
        raise AssertionError('expected ValueError')
