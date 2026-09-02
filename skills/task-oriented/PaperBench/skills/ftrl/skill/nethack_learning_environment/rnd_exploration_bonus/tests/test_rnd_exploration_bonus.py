from rnd_bonus import novelty_loss, update_predictor, intrinsic_reward, combined_reward

def test_novelty_decreases_after_update():
    features = {'distance': 4.0, 'hp': 1.0}
    target = {'distance': 0.5, 'hp': 0.2}
    predictor = {'distance': 0.0, 'hp': 0.0}
    before = novelty_loss(features, target, predictor)
    after_params = update_predictor(features, target, predictor, lr=0.01)
    after = novelty_loss(features, target, after_params)
    assert after < before
    assert combined_reward(1.0, intrinsic_reward(before, 0.1)) > 1.0


def test_repeated_updates_keep_decreasing_novelty():
    from rnd_bonus import novelty_loss, update_predictor
    features = {'distance': 2.0, 'hp': 1.0}
    target = {'distance': 0.4, 'hp': 0.1}
    predictor = {'distance': 0.0, 'hp': 0.0}
    losses = []
    for _ in range(4):
        losses.append(novelty_loss(features, target, predictor))
        predictor = update_predictor(features, target, predictor, lr=0.02)
    assert losses[-1] < losses[0]
