from replay_protocol import run_iteration

def test_buffer_order_and_replay_count():
    out = run_iteration([{'id':'old'}], [{'id':'new1'}, {'id':'new2'}], max_size=2, replay_updates=2, batch_size=1)
    assert [x['id'] for x in out['buffer']] == ['new1', 'new2']
    assert out['on_policy_batch_ids'] == ['new1', 'new2']
    assert out['trace'] == ['append_fresh_rollouts','on_policy_update','off_policy_replay_updates']
