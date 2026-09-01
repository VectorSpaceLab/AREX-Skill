from project_reward import project_reward

def test_sparse_and_composite_projection():
    out = project_reward([[1,0],[0,1],[2,3]],[{'index':0,'reward':2},{'index':2,'reward':0.5}])
    assert out['z_R'] == [3.0, 1.5]
    assert out['reward_count'] == 2
