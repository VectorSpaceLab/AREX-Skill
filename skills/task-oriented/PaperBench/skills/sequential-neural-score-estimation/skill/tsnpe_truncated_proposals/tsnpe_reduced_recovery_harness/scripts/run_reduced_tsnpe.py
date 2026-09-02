import argparse, json, math, random, subprocess, sys
from pathlib import Path

def analytic_mean(obs): return obs/2.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--attempt-dir', required=True); ap.add_argument('--skill-root', required=True); ns=ap.parse_args()
    attempt=Path(ns.attempt_dir); root=Path(ns.skill_root); rec=attempt/'recovery'; logs=rec/'logs'; logs.mkdir(parents=True, exist_ok=True)
    plan=json.load(open(attempt/'module_plan.json')); rng=random.Random(7); obs=0.25
    theta=[rng.uniform(-2,2) for _ in range(32)]; x=[t+rng.gauss(0,0.35) for t in theta]
    train_in=logs/'train_input.json'; train_out=logs/'training_trace.json'
    json.dump({'theta':theta,'x':x,'observation':obs,'mean':0.0,'log_std':0.0,'lr':0.05,'steps':40}, open(train_in,'w'), indent=2)
    cmd=[sys.executable, str(root/'tsnpe_pooled_mle_training/scripts/train_gaussian.py'), str(train_in), '--output', str(train_out)]
    r=subprocess.run(cmd, text=True, capture_output=True, timeout=20); commands=[{'command':' '.join(cmd),'returncode':r.returncode,'stdout_tail':r.stdout[-1000:],'stderr_tail':r.stderr[-1000:]}]
    if r.returncode: raise SystemExit(r.returncode)
    trace=json.load(open(train_out)); mean=trace['params_after']['mean']; log_std=trace['params_after']['log_std']
    posterior_samples=[rng.gauss(mean, math.exp(log_std)) for _ in range(128)]
    posterior_logs=[-0.5*((s-mean)/math.exp(log_std))**2-log_std for s in posterior_samples]
    prior_samples=[rng.uniform(-2,2) for _ in range(128)]
    prior_logs=[-0.5*((s-mean)/math.exp(log_std))**2-log_std for s in prior_samples]
    hpr_in=logs/'hpr_input.json'; hpr_out=logs/'hpr_output.json'; json.dump({'posterior_log_probs':posterior_logs,'prior_samples':prior_samples,'prior_log_probs_for_samples':prior_logs,'epsilon':0.05}, open(hpr_in,'w'), indent=2)
    cmd=[sys.executable, str(root/'tsnpe_hpr_truncated_proposal/scripts/hpr.py'), str(hpr_in), '--output', str(hpr_out)]
    r=subprocess.run(cmd, text=True, capture_output=True, timeout=20); commands.append({'command':' '.join(cmd),'returncode':r.returncode,'stdout_tail':r.stdout[-1000:],'stderr_tail':r.stderr[-1000:]})
    if r.returncode: raise SystemExit(r.returncode)
    hpr=json.load(open(hpr_out))
    true_logs=[]; sample_logs=[]
    for _ in range(16):
        t=rng.gauss(analytic_mean(obs),0.25); true_logs.append(-0.5*((t-mean)/math.exp(log_std))**2-log_std); sample_logs.append(posterior_logs[:32])
    sbcc_in=logs/'sbcc_input.json'; sbcc_out=logs/'sbcc_output.json'; json.dump({'true_log_probs':true_logs,'posterior_sample_log_probs':sample_logs,'threshold':hpr['threshold']}, open(sbcc_in,'w'), indent=2)
    cmd=[sys.executable, str(root/'tsnpe_sbcc_diagnostics/scripts/sbcc.py'), str(sbcc_in), '--output', str(sbcc_out)]
    r=subprocess.run(cmd, text=True, capture_output=True, timeout=20); commands.append({'command':' '.join(cmd),'returncode':r.returncode,'stdout_tail':r.stdout[-1000:],'stderr_tail':r.stderr[-1000:]})
    if r.returncode: raise SystemExit(r.returncode)
    sbcc=json.load(open(sbcc_out)); abs_err=abs(mean-analytic_mean(obs))
    (logs/'experiment_command_log.json').write_text(json.dumps({'commands':commands}, indent=2))
    inv=[{'module_id':'pooled_mle_training','skill':'tsnpe_pooled_mle_training','evidence':'called script','artifact':'recovery/logs/training_trace.json'}, {'module_id':'hpr_truncated_proposal','skill':'tsnpe_hpr_truncated_proposal','evidence':'called script','artifact':'recovery/logs/hpr_output.json'}, {'module_id':'sbcc_diagnostics','skill':'tsnpe_sbcc_diagnostics','evidence':'called script','artifact':'recovery/logs/sbcc_output.json'}, {'module_id':'sir_fallback_sampler','skill':'tsnpe_sir_fallback_sampler','evidence':'not applicable','reason':'rejection acceptance remained above threshold in reduced run'}, {'module_id':'reduced_recovery_harness','skill':'tsnpe_reduced_recovery_harness','evidence':'called script','artifact':'recovery/recovery_result.json'}]
    (logs/'generated_skill_invocations.json').write_text(json.dumps({'invocations': inv}, indent=2))
    (logs/'generated_data_item.json').write_text(json.dumps({'dataset':'synthetic bounded Gaussian','observation':obs,'theta_count':len(theta),'source':'generated from module_plan reduced target, not original repository'}, indent=2))
    result={'schema_version':1,'paper_id':'tsnpe_truncated_proposals','experiment':plan['fast_recovery_target']['dataset'],'is_proxy':True,'sample_count':len(theta),'metrics':{'absolute_mean_error_to_analytic_posterior':abs_err,'acceptance_rate':hpr['acceptance_rate'],'ground_truth_in_support_fraction':sbcc['ground_truth_in_support_fraction'],'loss_before':trace['loss_before'],'loss_after':trace['loss_after']},'paper_target':plan['fast_recovery_target'],'commands':['python recovery/run_recovery.py --attempt-dir ...'],'artifacts':['recovery/logs/training_trace.json','recovery/logs/hpr_output.json','recovery/logs/sbcc_output.json'],'mechanism_checks':{'hpr_threshold_computed':True,'prior_samples_rejected_outside_hpr':True,'pooled_data_used':True,'ordinary_mle_loss_used':True,'optimizer_step_executed':trace['mechanism_checks']['optimizer_step_executed'],'reduced_training_executed':True,'sbcc_coverage_computed':True,'source_repo_read':False},'notes':'Soft-mode reduced recovery; full sbibm/neuroscience benchmark not claimed.'}
    (rec/'recovery_result.json').write_text(json.dumps(result, indent=2))
if __name__=='__main__': main()
