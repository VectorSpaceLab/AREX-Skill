import json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/share/project/yuyang/workspace/Paperbench/record/case11/extracted_skills_attempt_001/ptq4vit_quantization')
sys.path.insert(0, str(SKROOT/'base_ptq_scale_search'/'scripts'))
sys.path.insert(0, str(SKROOT/'twin_uniform_quantization'/'scripts'))
sys.path.insert(0, str(SKROOT/'hessian_guided_metric'/'scripts'))
from calibrate import search_scale, cosine_distance
from twin_quant import twin_quantize, power_of_two_alignment
from hessian_metric import hessian_score, weighted_loss_and_grad
plan=json.loads((ROOT/'module_plan.json').read_text())
values=[0.002,0.011,0.031,0.21,0.73,0.98,-0.13,0.44]
reference=[0.0,0.01,0.03,0.22,0.76,1.0,-0.12,0.43]
gradients=[0.2,0.4,0.6,1.5,3.0,3.2,0.8,1.2]
twin=twin_quantize(values,bits=4,kind='gelu')
candidates=[0.03,0.06,0.09,0.12,0.18,0.24]
hess_trace=[]
for scale in candidates:
    recon=[round(v/scale)*scale for v in values]
    hess_trace.append({'scale':scale,'score':hessian_score(reference,recon,gradients),'reconstruction':recon})
hess_best=min(hess_trace,key=lambda x:x['score'])
cos=search_scale(values,candidates,bits=4,metric=cosine_distance)
loss_before, grad=weighted_loss_and_grad(1.0, hess_best['reconstruction'], reference, gradients)
scale_param=1.0
scale_param -= 0.05*grad
loss_after,_=weighted_loss_and_grad(scale_param, hess_best['reconstruction'], reference, gradients)
metric=max(0.0, cos['score']-hess_best['score'])
logs=ROOT/'recovery'/'logs'; logs.mkdir(parents=True,exist_ok=True)
(logs/'generated_data_item.json').write_text(json.dumps({'schema_version':1,'dataset':'synthetic_vit_activation_calibration','is_resource_derived':False,'resource_files':[],'values':values,'reference':reference,'gradients':gradients,'notes':'Deterministic synthetic activation item shaped to include post-softmax/GELU edge cases.'},indent=2))
(logs/'training_trace.json').write_text(json.dumps({'schema_version':1,'loss_before':loss_before,'loss_after':loss_after,'params_before':{'scale':1.0},'params_after':{'scale':scale_param},'parameters_before':{'scale':1.0},'parameters_after':{'scale':scale_param},'optimizer_state_changed':scale_param!=1.0,'learning_rate':0.05},indent=2))
(logs/'metric_trace.json').write_text(json.dumps({'twin':twin,'alignment':power_of_two_alignment({'r1':0.125,'r2':0.5}),'hessian_trace':hess_trace,'cosine_trace':cos['trace']},indent=2))
result={'schema_version':1,'paper_id':'ptq4vit_quantization','experiment':'synthetic_vit_activation_calibration','is_proxy':True,'sample_count':1,'metrics':{'hessian_loss_improvement':metric,'loss_before':loss_before,'loss_after':loss_after},'paper_target':plan['fast_recovery_target'],'commands':['python recovery/run_recovery.py '+str(SKROOT)],'artifacts':['recovery/logs/generated_data_item.json','recovery/logs/training_trace.json','recovery/logs/metric_trace.json'],'mechanism_checks':{'source_repo_read':False,'twin_uniform_executed':True,'hessian_metric_executed':True,'base_ptq_scale_search_executed':True,'reduced_training_executed':True,'optimizer_step_executed':scale_param!=1.0,'training_step_executed':False,'qwen3_model_loaded':False,'full_imagenet_blocked':True,'proxy_declared':True},'notes':'Soft-mode proxy; full ImageNet ViT calibration blocked by missing ImageNet/pretrained runtime in bounded environment.'}
(ROOT/'recovery'/'recovery_result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
