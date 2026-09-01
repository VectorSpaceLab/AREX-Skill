#!/usr/bin/env python3
import argparse, json, math

def _mean(values): return sum(values)/len(values)
def _mse(values): return _mean([v*v for v in values])

def run_sac_update(batch, params=None, gamma=0.99, alpha=0.2, lr=0.05, tau=0.1):
    transitions=batch.get('transitions', batch)
    if not transitions:
        raise ValueError('transitions are required')
    params_before=dict(params or {'value':0.0,'q1':0.2,'q2':0.1,'policy':0.0,'target_value':0.0})
    for key in ['value','q1','q2','policy','target_value']:
        params_before[key]=float(params_before[key])
    rewards=[float(t['reward']) for t in transitions]
    log_probs=[float(t['log_prob']) for t in transitions]
    min_q=min(params_before['q1'], params_before['q2'])
    soft_targets=[min_q - alpha*lp for lp in log_probs]
    q_targets=[r + gamma*params_before['target_value']*(0.0 if bool(t.get('done')) else 1.0) for r,t in zip(rewards, transitions)]
    value_errors=[params_before['value'] - target for target in soft_targets]
    q1_errors=[params_before['q1'] - target for target in q_targets]
    q2_errors=[params_before['q2'] - target for target in q_targets]
    actor_terms=[alpha*lp - min_q + 0.1*params_before['policy'] for lp in log_probs]
    loss_before=_mse(value_errors)+_mse(q1_errors)+_mse(q2_errors)+abs(_mean(actor_terms))
    params_after=dict(params_before)
    params_after['value'] -= lr*_mean(value_errors)
    params_after['q1'] -= lr*_mean(q1_errors)
    params_after['q2'] -= lr*_mean(q2_errors)
    params_after['policy'] -= lr*_mean(actor_terms)
    params_after['target_value'] = tau*params_after['value'] + (1.0-tau)*params_before['target_value']
    min_q_after=min(params_after['q1'], params_after['q2'])
    value_errors_after=[params_after['value'] - (min_q_after - alpha*lp) for lp in log_probs]
    q_targets_after=[r + gamma*params_after['target_value']*(0.0 if bool(t.get('done')) else 1.0) for r,t in zip(rewards, transitions)]
    q1_errors_after=[params_after['q1'] - target for target in q_targets_after]
    q2_errors_after=[params_after['q2'] - target for target in q_targets_after]
    actor_terms_after=[alpha*lp - min_q_after + 0.1*params_after['policy'] for lp in log_probs]
    loss_after=_mse(value_errors_after)+_mse(q1_errors_after)+_mse(q2_errors_after)+abs(_mean(actor_terms_after))
    checks={'entropy_term_used': True, 'replay_batch_used': len(transitions)>0, 'twin_q_min_used': True, 'value_update_executed': params_after['value'] != params_before['value'], 'q_update_executed': params_after['q1'] != params_before['q1'] and params_after['q2'] != params_before['q2'], 'policy_update_executed': params_after['policy'] != params_before['policy'], 'polyak_target_update_executed': params_after['target_value'] != params_before['target_value'], 'optimizer_step_executed': params_after != params_before, 'reduced_training_executed': True, 'training_step_executed': False, 'qwen3_model_loaded': False}
    return {'loss_before': loss_before, 'loss_after': loss_after, 'params_before': params_before, 'params_after': params_after, 'mechanism_checks': checks}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    data=json.load(open(args.input))
    result=run_sac_update(data.get('batch', data), data.get('params'), data.get('gamma',0.99), data.get('alpha',0.2), data.get('lr',0.05), data.get('tau',0.1))
    json.dump(result, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
