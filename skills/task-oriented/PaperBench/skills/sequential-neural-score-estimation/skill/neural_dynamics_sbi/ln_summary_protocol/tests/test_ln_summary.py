import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from ln_summary import compute_summary, dot, simulate_ln


def test_simulate_ln_summary_shape_and_rate():
    item = simulate_ln([1.0, -0.5, 0.25], n_stimuli=96, seed=3)
    assert len(item["summary"]) == 4
    assert 0.0 <= item["firing_rate"] <= 1.0
    assert len(item["spikes"]) == 96


def test_compute_summary_no_spikes_is_stable():
    summary, sta, firing_rate = compute_summary([[1.0, 2.0], [3.0, 4.0]], [0, 0])
    assert summary == [0.0, 0.0, 0.0]
    assert sta == [0.0, 0.0]
    assert firing_rate == 0.0


def test_sta_aligns_with_positive_filter_signal():
    item = simulate_ln([1.2, 0.0], n_stimuli=400, seed=11, bias=-1.0, gain=2.0)
    assert dot(item["sta"], [1.2, 0.0]) > 0.0
