import math
from logprob_accounting import sequence_logprob, batch_sequence_logprob, log_softmax

def test_masks_prompt_and_padding_tokens():
    log_probs = [[math.log(.5), math.log(.5)], [math.log(.9), math.log(.1)], [math.log(.2), math.log(.8)]]
    got = sequence_logprob(log_probs, [-100, 0, -100])
    assert abs(got["logprob"] - math.log(.9)) < 1e-9
    assert got["token_count"] == 1

def test_average_option():
    log_probs = [[math.log(.5), math.log(.5)], [math.log(.25), math.log(.75)]]
    got = sequence_logprob(log_probs, [0, 1], average=True)
    assert abs(got["logprob"] - ((math.log(.5)+math.log(.75))/2)) < 1e-9

def test_rejects_zero_unmasked_tokens():
    try:
        sequence_logprob([[0.0]], [-100])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "zero" in str(exc)

def test_batch_sequence_logprob():
    assert batch_sequence_logprob([[[0.0]]], [[0]]) == [0.0]
    row = log_softmax([1.0, 2.0])
    assert abs(sum(math.exp(x) for x in row) - 1.0) < 1e-9


def test_rejects_invalid_label_id():
    try:
        sequence_logprob([[0.0, -1.0]], [3])
        assert False, "expected invalid label failure"
    except ValueError as exc:
        assert "invalid label" in str(exc)
