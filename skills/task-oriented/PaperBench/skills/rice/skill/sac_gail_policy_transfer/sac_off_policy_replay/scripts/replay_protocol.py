#!/usr/bin/env python3
import argparse, copy, json, math
REQUIRED=('state','action','reward','next_state','done','log_prob')

def _finite(value, name):
    number=float(value)
    if not math.isfinite(number):
        raise ValueError(f'{name} must be finite')
    return number

def validate_transition(item):
    missing=[key for key in REQUIRED if key not in item]
    if missing:
        raise ValueError(f'missing transition fields: {missing}')
    return {'state': _finite(item['state'],'state'), 'action': _finite(item['action'],'action'), 'reward': _finite(item['reward'],'reward'), 'next_state': _finite(item['next_state'],'next_state'), 'done': bool(item['done']), 'log_prob': _finite(item['log_prob'],'log_prob')}

def build_replay_batch(transitions, indices=None):
    buffer=[validate_transition(t) for t in transitions]
    if not buffer:
        raise ValueError('replay buffer is empty')
    if indices is None:
        indices=list(range(len(buffer)))
    sampled=[]
    for idx in indices:
        sampled.append(copy.deepcopy(buffer[int(idx) % len(buffer)]))
    return {'size': len(buffer), 'sample_count': len(sampled), 'transitions': sampled}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    data=json.load(open(args.input))
    result=build_replay_batch(data['transitions'], data.get('indices'))
    json.dump(result, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
