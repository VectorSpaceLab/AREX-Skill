import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cdc_similarity_loss' / 'scripts'))
from adapt_step import finite_difference_step


def test_optimizer_step_changes_params_and_reduces_loss():
    source = [[0.0, 0.0], [1.0, 0.2], [0.2, 1.0], [1.0, 1.0]]
    anchors = [[0.2, 0.1], [1.1, 1.0]]
    routes = [{'index':0,'route':'image'}, {'index':1,'route':'patch'}, {'index':2,'route':'patch'}, {'index':3,'route':'image'}]
    result = finite_difference_step(source, {'scale': 0.7, 'bias': 0.4}, anchors, routes, {'cdc': 1.0, 'image': 2.0, 'patch': 0.05}, lr=0.15)
    assert result['params_before'] != result['params_after']
    assert result['loss_after'] < result['loss_before']
