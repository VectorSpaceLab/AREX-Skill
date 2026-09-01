import math

from conditional_nce_protocol import ConditionalNCEProtocol, build_section_4_3_protocol, section_4_3_partitions


def test_section_4_3_distribution_and_partitions():
    protocol = build_section_4_3_protocol(k_negatives=2)
    assert section_4_3_partitions() == {"x1": 4.0, "x2": 6.0}
    assert math.isclose(protocol.p_y_given_x["x1"]["y1"], 0.25)
    assert math.isclose(protocol.p_y_given_x["x1"]["y2"], 0.75)
    assert math.isclose(protocol.p_y_given_x["x2"]["y1"], 0.5)
    assert math.isclose(protocol.conditional_ratio("x1", "y1", "y2"), 1.0 / 3.0)


def test_adjusted_score_and_population_mass():
    protocol = build_section_4_3_protocol(k_negatives=1)
    assert math.isclose(protocol.bar_score(math.log(3.0), "y1"), math.log(6.0))
    events = protocol.enumerate_population_events()
    assert len(events) == 8
    assert math.isclose(sum(item["probability"] for item in events), 1.0)


def test_protocol_rejects_invalid_contracts():
    try:
        build_section_4_3_protocol(k_negatives=0)
        raise AssertionError("expected invalid K to be rejected")
    except ValueError as exc:
        assert "k_negatives" in str(exc)

    try:
        ConditionalNCEProtocol(
            inputs=("x",),
            labels=("a", "b"),
            p_x={"x": 1.0},
            p_y_given_x={"x": {"a": 0.7, "b": 0.7}},
            p_noise={"a": 0.5, "b": 0.5},
            k_negatives=1,
        )
        raise AssertionError("expected invalid conditional distribution to be rejected")
    except ValueError as exc:
        assert "sum to 1.0" in str(exc)

    try:
        ConditionalNCEProtocol(
            inputs=("x",),
            labels=("a", "b"),
            p_x={"x": 1.0},
            p_y_given_x={"x": {"a": 0.5, "b": 0.5}},
            p_noise={"a": 1.0, "b": 0.0},
            k_negatives=1,
        )
        raise AssertionError("expected zero noise mass to be rejected")
    except ValueError as exc:
        assert "positive" in str(exc)
