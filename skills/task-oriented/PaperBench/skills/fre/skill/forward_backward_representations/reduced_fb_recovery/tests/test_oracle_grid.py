from oracle_grid import shortest_path_oracle

def test_oracle_prefers_goal_direction():
    policy = shortest_path_oracle(3, 3, (2, 2))
    assert 3 in policy[0] or 1 in policy[0]
    assert policy[8] == [1, 3]
