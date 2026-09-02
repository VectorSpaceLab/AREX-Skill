from race_protocol import accuracy, build_candidates, predict_from_logits


def test_build_candidates_creates_four_labeled_records():
    item = build_candidates(
        "A new store opened beside the mall.",
        "What opened beside the mall?",
        ["a store", "a park", "a school", "a station"],
        "A",
    )
    assert [candidate["label"] for candidate in item["candidates"]] == ["A", "B", "C", "D"]
    assert item["candidates"][0]["is_gold"] is True
    assert "what" in item["candidates"][0]["tokens"]


def test_predict_and_accuracy():
    predicted = predict_from_logits({"A": 0.2, "B": 1.2, "C": -0.1, "D": 0.0})
    assert predicted == "B"
    assert accuracy(predicted, "B") == 1.0
    assert accuracy(predicted, "A") == 0.0


def test_rejects_non_race_option_count():
    try:
        build_candidates("article", "question", ["one", "two"], "A")
    except ValueError as exc:
        assert "exactly four" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_truncation_respects_max_sequence_length():
    article = " ".join(["context"] * 80) + " answer clue near beginning"
    item = build_candidates(
        article,
        "Which option is supported?",
        ["answer clue", "wrong option", "another distractor", "last distractor"],
        "A",
        max_seq_len=32,
    )
    assert all(len(candidate["tokens"]) <= 32 for candidate in item["candidates"])
    assert item["candidates"][0]["tokens"][0] == "[CLS]"
    assert item["candidates"][0]["tokens"][-1] == "[SEP]"
