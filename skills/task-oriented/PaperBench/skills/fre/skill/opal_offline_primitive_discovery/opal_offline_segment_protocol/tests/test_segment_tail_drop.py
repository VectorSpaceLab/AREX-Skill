from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from segment_trajectories import segment_trajectories


def test_tail_drop_is_reported_without_padding():
    result = segment_trajectories([{'states': [0, 1, 2, 3, 4], 'actions': [1, 1, 1, 1]}], 3)
    assert result['summary']['segment_count'] == 1
    assert result['summary']['dropped_tails'] == 1
    assert len(result['segments'][0]['actions']) == 3


if __name__ == '__main__':
    test_tail_drop_is_reported_without_padding()
