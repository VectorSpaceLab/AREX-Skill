from rnd_model import make_matrix, train_predictor


def test_predictor_learns_without_mutating_target():
    target = make_matrix(3, 2, seed=7)
    predictor = make_matrix(3, 2, seed=11)
    trace = train_predictor(target, predictor, [[1.0, 0.0], [0.9, 0.1]], lr=0.2, steps=60)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["target_unchanged"] is True
    assert trace["predictor_changed"] is True
