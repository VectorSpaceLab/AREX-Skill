from entropy_objective import soft_objective

def test_entropy_bonus_increases_soft_return():
    out=soft_objective([1.0, 0.0], [-0.5, -1.0], gamma=1.0, alpha=0.2)
    assert out['soft_return'] > out['reward_return']
    assert out['entropy_bonuses'] == [0.1, 0.2]

def test_zero_alpha_matches_reward_return():
    out=soft_objective([1.0, 2.0], [-5.0, -1.0], gamma=0.5, alpha=0.0)
    assert out['soft_return'] == out['reward_return']
