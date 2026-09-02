from corpus_protocol import build_protocol


def test_build_protocol_valid_split():
    protocol = build_protocol(
        ["target_alpha", {"id": "t1", "text": "target_beta"}],
        [{"id": "h0", "text": "heldout_gamma", "category": "proxy"}],
    )
    assert protocol["split_checks"]["train_count"] == 2
    assert protocol["categories"] == ["proxy"]


def test_overlap_rejected():
    try:
        build_protocol(["same_text"], ["same_text"])
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("expected overlap rejection")


def test_disallowed_marker_rejected():
    try:
        build_protocol(["safe marker"], ["heldout"], disallowed_markers=["marker"])
    except ValueError as exc:
        assert "disallowed" in str(exc)
    else:
        raise AssertionError("expected marker rejection")


def test_duplicate_train_ids_rejected():
    try:
        build_protocol([{"id": "dup", "text": "one"}, {"id": "dup", "text": "two"}], ["heldout"])
    except ValueError as exc:
        assert "duplicate id" in str(exc)
    else:
        raise AssertionError("expected duplicate id rejection")
