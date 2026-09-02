import argparse, json

def run_iteration(buffer, fresh_rollouts, max_size=100, replay_updates=1, batch_size=2):
    if replay_updates < 0 or batch_size <= 0:
        raise ValueError('invalid replay settings')
    new_buffer = list(buffer) + list(fresh_rollouts)
    if len(new_buffer) > max_size:
        new_buffer = new_buffer[-max_size:]
    fresh_ids = [item.get('id', str(i)) for i, item in enumerate(fresh_rollouts)]
    replay_batches = []
    for update in range(replay_updates):
        start = (update * batch_size) % max(1, len(new_buffer))
        batch = [new_buffer[(start + j) % len(new_buffer)] for j in range(min(batch_size, len(new_buffer)))] if new_buffer else []
        replay_batches.append({'update_index': update, 'items': batch, 'source_ids': [x.get('id','') for x in batch]})
    return {'buffer': new_buffer, 'on_policy_batch_ids': fresh_ids, 'replay_batches': replay_batches, 'trace': ['append_fresh_rollouts','on_policy_update','off_policy_replay_updates']}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    out = run_iteration([{'id':'old'}], [{'id':'new1'}, {'id':'new2'}], max_size=2, replay_updates=2, batch_size=1)
    if a.self_test:
        assert [x['id'] for x in out['buffer']] == ['new1','new2']
        assert out['trace'][1] == 'on_policy_update'
        assert len(out['replay_batches']) == 2
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
