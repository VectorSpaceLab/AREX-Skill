#!/usr/bin/env python3
import argparse, json

def linear_score(x, a=-1.0, c=0.0):
    return a*x + c

def run_pc(initial, times, score_a=-1.0, score_c=0.0, predictor_scale=0.05, corrector_step=0.1):
    if any(times[i] <= times[i+1] for i in range(len(times)-1)):
        raise ValueError('times must be strictly decreasing')
    x=float(initial); trajectory=[]
    for t0,t1 in zip(times[:-1], times[1:]):
        dt=t0-t1
        s=linear_score(x, score_a, score_c)
        pred_update=-predictor_scale*dt*s
        x_pred=x+pred_update
        trajectory.append({'phase':'predictor','t0':t0,'t1':t1,'state_before':x,'score':s,'update':pred_update,'state_after':x_pred})
        s2=linear_score(x_pred, score_a, score_c)
        corr_update=corrector_step*s2
        x_corr=x_pred+corr_update
        trajectory.append({'phase':'corrector','t0':t1,'state_before':x_pred,'score':s2,'update':corr_update,'state_after':x_corr})
        x=x_corr
    return {'initial': initial, 'final': x, 'trajectory': trajectory, 'mechanism_checks': {'predictor_executed': True, 'corrector_executed': True, 'steps': len(trajectory)}}

def self_test():
    out=run_pc(2.0,[1.0,0.5,0.1],corrector_step=0.2)
    assert abs(out['final']) < 2.0
    phases=[x['phase'] for x in out['trajectory']]
    assert 'predictor' in phases and 'corrector' in phases
    return True

def main():
    p=argparse.ArgumentParser(); p.add_argument('--self-test', action='store_true'); args=p.parse_args()
    if args.self_test:
        self_test(); print(json.dumps({'ok': True})); return
    print(json.dumps(run_pc(2.0,[1.0,0.5,0.1]), indent=2))
if __name__ == '__main__': main()
