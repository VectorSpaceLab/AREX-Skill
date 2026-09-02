#!/usr/bin/env python3
import argparse, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'atomic_loss_training' / 'scripts'))
from atomic_loss import normal_logpdf, one_step

def analytic_posterior_mean(obs, prior_var=1.0, noise_var=0.25):
    return (prior_var/(prior_var+noise_var))*obs

def run_proxy(obs=0.6, rounds=2, simulations_per_round=32, proposal_scale=1.0):
    proposal_mean=0.0; proposal_std=1.0; params={'w':0.05,'b':0.0}; round_logs=[]; trace=None
    base_atoms=[-1.2,-0.5,0.0,0.3,0.48,0.75,1.1,1.6]
    for r in range(rounds):
        atoms=[proposal_mean + proposal_std*proposal_scale*a for a in base_atoms]
        positive=min(range(len(atoms)), key=lambda i: abs(atoms[i]-obs))
        prior=[normal_logpdf(a,0.0,1.0) for a in atoms]
        proposal=[normal_logpdf(a,proposal_mean,proposal_std) for a in atoms]
        trace=one_step(atoms, obs, positive, params, prior, proposal, lr=0.4)
        params=trace['params_after']
        weights=[]
        for a,p,q in zip(atoms, prior, proposal):
            score=params['w']*(-(a-obs)**2)+params['b']*a
            weights.append(math.exp(score + q - p))
        total=sum(weights); posterior_mean=sum(a*w for a,w in zip(atoms,weights))/total
        round_logs.append({'round':r+1,'proposal_mean_before':proposal_mean,'proposal_std_before':proposal_std,'posterior_mean_estimate':posterior_mean,'positive_atom':atoms[positive],'loss_before':trace['loss_before'],'loss_after':trace['loss_after']})
        proposal_mean=0.5*proposal_mean+0.5*posterior_mean; proposal_std=max(0.35, proposal_std*0.75)
    target=analytic_posterior_mean(obs)
    return {'observed_x':obs,'rounds':round_logs,'final_proposal_mean':proposal_mean,'analytic_posterior_mean':target,'posterior_mean_abs_error':abs(proposal_mean-target),'training_trace':trace,'sample_count':rounds*simulations_per_round}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output'); ap.add_argument('--self-test', action='store_true'); ap.add_argument('--obs', type=float, default=0.6); ap.add_argument('--rounds', type=int, default=2); ap.add_argument('--simulations-per-round', type=int, default=32); ap.add_argument('--proposal-scale', type=float, default=1.0); ns=ap.parse_args()
    out=run_proxy(obs=ns.obs, rounds=ns.rounds, simulations_per_round=ns.simulations_per_round, proposal_scale=ns.proposal_scale)
    if ns.self_test:
        assert out['posterior_mean_abs_error'] < abs(out['analytic_posterior_mean'])
        assert out['training_trace']['params_before'] != out['training_trace']['params_after']
    if ns.output: Path(ns.output).write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
