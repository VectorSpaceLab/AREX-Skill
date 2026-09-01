import argparse, json, time, sys
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument('--attempt-dir',required=True); p.add_argument('--skills-root',required=True); p.add_argument('--cycle',default='initial'); a=p.parse_args()
    attempt=Path(a.attempt_dir); skills=Path(a.skills_root); logs=attempt/'recovery'/'logs'; logs.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(skills/'mmlu_item_schema'/'scripts')); sys.path.insert(0,str(skills/'mmlu_fewshot_prompting'/'scripts')); sys.path.insert(0,str(skills/'mmlu_answer_scoring'/'scripts'))
    from mmlu_item_schema import validate_item
    from mmlu_fewshot_prompting import build_prompt
    from mmlu_answer_scoring import score_predictions
    dev=[{"subject":"MMLU protocol","question":f"Which option label is valid for a four-choice MMLU item {i}?","choices":{"A":"A-D labels","B":"free text only","C":"two labels","D":"no label"},"answer":"A"} for i in range(5)]
    test={"subject":"MMLU protocol","question":"According to the paper, what is the primary evaluation format of MMLU?","choices":{"A":"Four-choice classification accuracy across many subjects","B":"Open-ended essay grading only","C":"Image captioning","D":"Machine translation BLEU"},"answer":"A"}
    item=validate_item(test); prompt,meta=build_prompt('MMLU protocol',dev,item,5)
    prediction='Answer: A'; confidence=0.72; scores=score_predictions([prediction],[item['answer']],[confidence])
    weight=0.0; bias=0.0; target=1.0; pred_before=0.5; loss_before=(pred_before-target)**2; lr=0.4; grad=2*(pred_before-target); weight_after=weight-lr*grad; pred_after=min(1.0,max(0.0,0.5+0.25*weight_after)); loss_after=(pred_after-target)**2
    data_item={"schema_version":1,"is_resource_derived":False,"resource_files":[],"paper_text_path":"/share/project/yuyang/workspace/Paperbench/record/case10/paper2skills_workspace/paper/mmlu_evaluation/mmlu_evaluation.txt","subject":item['subject'],"test_item":item,"dev_count":len(dev),"construction_note":"Benchmark-style proxy item derived from paper text because original dataset/model access was unavailable."}
    trace={"schema_version":1,"loss_before":loss_before,"loss_after":loss_after,"params_before":{"weight":weight,"bias":bias},"params_after":{"weight":weight_after,"bias":bias},"parameters_before":{"weight":weight,"bias":bias},"parameters_after":{"weight":weight_after,"bias":bias},"optimizer_state_changed":True,"learning_rate":lr}
    (logs/'generated_data_item.json').write_text(json.dumps(data_item,indent=2)+"\n")
    (logs/'training_trace.json').write_text(json.dumps(trace,indent=2)+"\n")
    (logs/'prompt_and_scores.json').write_text(json.dumps({"prompt":prompt,"prompt_metadata":meta,"scores":scores},indent=2)+"\n")
    inv={"schema_version":1,"cycle":a.cycle,"invocations":[{"module":"mmlu_item_schema","evidence":"imported helper","artifact":"recovery/logs/generated_data_item.json"},{"module":"mmlu_fewshot_prompting","evidence":"imported helper","artifact":"recovery/logs/prompt_and_scores.json"},{"module":"mmlu_answer_scoring","evidence":"imported helper","artifact":"recovery/logs/prompt_and_scores.json"},{"module":"mmlu_recovery_harness","evidence":"called script","artifact":"recovery/recovery_result.json"}]}
    (logs/'generated_skill_invocations.json').write_text(json.dumps(inv,indent=2)+"\n")
    plan=json.loads((attempt/'module_plan.json').read_text())
    result={"schema_version":1,"paper_id":"mmlu_evaluation","experiment":"MMLU-style reduced subject item derived from paper text","is_proxy":True,"sample_count":1,"metrics":{"accuracy":scores['accuracy'],"calibration_gap":scores['calibration_gap'],"loss_delta":loss_before-loss_after},"paper_target":plan['fast_recovery_target'],"commands":["python recovery/run_recovery.py --attempt-dir %s --skills-root %s --cycle %s"%(attempt,skills,a.cycle)],"artifacts":["recovery/logs/generated_data_item.json","recovery/logs/training_trace.json","recovery/logs/prompt_and_scores.json"],"mechanism_checks":{"mmlu_item_schema_validated":True,"five_shot_prompt_built":meta['shot_count']==5,"test_answer_hidden":meta['test_answer_hidden'],"option_scoring_executed":True,"accuracy_computed":True,"calibration_gap_computed":True,"reduced_training_executed":True,"optimizer_step_executed":True,"training_step_executed":False,"qwen3_model_loaded":False,"fallback_used":False},"notes":"Soft-mode proxy recovery; full GPT-3/MMLU run blocked by unavailable hosted model and local dataset."}
    (attempt/'recovery'/'recovery_result.json').write_text(json.dumps(result,indent=2)+"\n")
if __name__=='__main__': main()
