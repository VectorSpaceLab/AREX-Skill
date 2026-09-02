
import importlib.util, json, math, os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SKILLS=Path(__file__).resolve().parents[2]

def load_helper(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

forward = load_helper('forward_ddpm_utils', SKILLS/'forward_diffusion_schedule'/'scripts'/'ddpm_utils.py')
loss = load_helper('loss_ddpm_utils', SKILLS/'epsilon_prediction_loss'/'scripts'/'ddpm_utils.py')
reverse = load_helper('reverse_ddpm_utils', SKILLS/'reverse_sampling_posterior'/'scripts'/'ddpm_utils.py')
linear_beta_schedule = forward.linear_beta_schedule
coefficients = forward.coefficients
q_sample_scalar = forward.q_sample_scalar
mse_loss = loss.mse_loss
gradient_step = loss.gradient_step
predict_epsilon = loss.predict_epsilon
predict_start_from_noise = reverse.predict_start_from_noise
posterior_mean_variance = reverse.posterior_mean_variance

def run(attempt_dir):
    attempt=Path(attempt_dir); rec=attempt/'recovery'; logs=rec/'logs'; logs.mkdir(parents=True, exist_ok=True)
    plan=json.loads((attempt/'module_plan.json').read_text())
    betas=linear_beta_schedule(0.0001,0.02,8); rows=coefficients(betas)
    x_values=[-0.75,-0.5,-0.25,0.0,0.25,0.5,0.75,1.0]
    eps_values=[0.31,-0.17,0.44,-0.28,0.13,-0.51,0.22,-0.09]
    samples=[]
    for i,(x,eps) in enumerate(zip(x_values,eps_values)):
        t=i%len(rows); row=rows[t]
        samples.append({'id':i,'x_start':x,'epsilon':eps,'t':t,'t_scaled':t/(len(rows)-1),'x_t':q_sample_scalar(x,eps,row)})
    theta=[0.0,0.0,0.0]
    loss_before=mse_loss(samples,theta)
    for _ in range(25): theta=gradient_step(samples,theta,0.35)
    loss_after=mse_loss(samples,theta)
    probe=samples[-1]; prow=rows[probe['t']]
    eps_hat=predict_epsilon(theta, probe['x_t'], probe['t_scaled'])
    x0_hat=predict_start_from_noise(probe['x_t'], eps_hat, prow)
    post=posterior_mean_variance(x0_hat, probe['x_t'], prow)
    data={'schema_version':1,'dataset':'synthetic_tiny_images','sample_count':len(samples),'is_resource_derived':False,'resource_files':[],'construction':'Deterministic scalar image-like samples in [-1,1] with fixed Gaussian-noise fixtures.','samples':samples}
    trace={'schema_version':1,'loss_before':loss_before,'loss_after':loss_after,'params_before':[0.0,0.0,0.0],'params_after':theta,'parameters_before':[0.0,0.0,0.0],'parameters_after':theta,'optimizer':'manual_gradient_descent','optimizer_state_changed':True,'steps':25,'learning_rate':0.35}
    inv={'schema_version':1,'invocations':[{'module':'forward_diffusion_schedule','skill':'forward_diffusion_schedule','evidence':'imported helper','artifact':'recovery/logs/generated_data_item.json'},{'module':'epsilon_prediction_loss','skill':'epsilon_prediction_loss','evidence':'imported helper','artifact':'recovery/logs/training_trace.json'},{'module':'reverse_sampling_posterior','skill':'reverse_sampling_posterior','evidence':'imported helper','artifact':'recovery/logs/reverse_step_check.json'},{'module':'reduced_ddpm_recovery_harness','skill':'reduced_ddpm_recovery_harness','evidence':'called script','artifact':'recovery/recovery_result.json'}]}
    reverse={'predicted_epsilon':eps_hat,'predicted_x0':x0_hat,'posterior':post}
    result={'schema_version':1,'paper_id':'ddpm_denoising_diffusion','experiment':'synthetic_tiny_images deterministic_8_examples','is_proxy':True,'sample_count':len(samples),'metrics':{'epsilon_mse_loss_reduction':loss_before-loss_after,'loss_before':loss_before,'loss_after':loss_after},'paper_target':plan['fast_recovery_target'],'commands':['python recovery/run_recovery.py'],'artifacts':['recovery/logs/generated_data_item.json','recovery/logs/training_trace.json','recovery/logs/reverse_step_check.json'],'mechanism_checks':{'forward_noising_executed':True,'epsilon_prediction_loss_executed':True,'reduced_training_executed':True,'optimizer_step_executed':True,'training_step_executed':False,'qwen3_model_loaded':False,'reverse_posterior_executed':True,'all_core_modules_invoked':True,'source_boundary_original_repo_used':False,'fallback_used':True},'notes':'Soft-mode reduced proxy; validates DDPM mechanism but not CIFAR-10 FID.'}
    (logs/'generated_data_item.json').write_text(json.dumps(data,indent=2))
    (logs/'training_trace.json').write_text(json.dumps(trace,indent=2))
    (logs/'reverse_step_check.json').write_text(json.dumps(reverse,indent=2))
    (logs/'generated_skill_invocations.json').write_text(json.dumps(inv,indent=2))
    (rec/'recovery_result.json').write_text(json.dumps(result,indent=2))
    return result
if __name__=='__main__':
    out=run(sys.argv[1] if len(sys.argv)>1 else ROOT)
    print(json.dumps(out,indent=2))
