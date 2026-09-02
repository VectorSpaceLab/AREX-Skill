from rnd_model import make_matrix, mse_errors, train_predictor


def test_target_error_reduces_on_small_shifted_batch():
    observations = [[1.0, 0.0, -0.1], [1.0, 0.1, 0.0], [0.9, 0.0, 0.1]]
    target = make_matrix(4, 3, seed=19)
    predictor = make_matrix(4, 3, seed=23)
    before = sum(mse_errors(target, predictor, observations)) / len(observations)
    trace = train_predictor(target, predictor, observations, lr=0.1, steps=90)
    after = sum(mse_errors(target, predictor, observations)) / len(observations)
    assert after < before
    assert trace['target_unchanged'] is True
