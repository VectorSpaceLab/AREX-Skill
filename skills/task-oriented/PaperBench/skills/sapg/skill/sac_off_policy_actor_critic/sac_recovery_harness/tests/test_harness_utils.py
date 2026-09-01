from harness_utils import build_replay_batch, summarize_batch

def test_batch_has_terminal_and_samples():
    batch=build_replay_batch(); summary=summarize_batch(batch)
    assert summary['sample_count'] == 6
    assert summary['has_terminal'] is True
    assert len(batch['rewards']) == len(batch['log_probs'])
