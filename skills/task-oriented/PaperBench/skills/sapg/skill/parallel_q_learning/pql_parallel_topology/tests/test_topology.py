from topology import build_topology, validate_topology


def test_topology_contains_required_roles_and_edges():
    topology = build_topology(8, 64, 2, 1, 2, 4)
    assert validate_topology(topology) == []
    assert "actors" in topology["roles"]
    assert ["policy_learner", "actors", "policy_sync"] in topology["edges"]
    assert topology["parameters"]["transitions_per_tick"] == 16


def test_invalid_environment_count_is_rejected():
    try:
        build_topology(0, 64, 1, 1, 1, 4)
    except ValueError as exc:
        assert "num_envs" in str(exc)
    else:
        raise AssertionError("expected ValueError")
