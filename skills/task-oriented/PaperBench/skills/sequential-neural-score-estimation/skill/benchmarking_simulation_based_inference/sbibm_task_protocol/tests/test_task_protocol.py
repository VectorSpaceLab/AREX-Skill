from task_protocol import build_gaussian_linear_task


def test_gaussian_linear_task_shapes_and_posterior():
    item = build_gaussian_linear_task(dim=3, prior_scale=1.0, simulator_scale=1.0, seed=1)
    assert item['dim_parameters'] == 3
    assert len(item['observation']) == 3
    assert item['posterior']['variance'] == 0.5
    assert item['simulation_budget'] == 256


def test_invalid_dimension_rejected():
    try:
        build_gaussian_linear_task(dim=0)
    except ValueError as exc:
        assert 'dim' in str(exc)
    else:
        raise AssertionError('expected ValueError')


def test_observation_dimension_mismatch_rejected():
    try:
        build_gaussian_linear_task(dim=3, observation=[1.0, 2.0])
    except ValueError as exc:
        assert 'observation length' in str(exc)
    else:
        raise AssertionError('expected ValueError')
