import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent/'task_configuration'/'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent/'model_adapter_interface'/'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent/'metric_aggregation'/'scripts'))
from task_config import format_instance
from adapter import DeterministicLM
from metrics import compute_metrics

def run_eval(cfg, docs):
    instances=[format_instance(cfg,d) for d in docs]
    lm=DeterministicLM(scores=cfg.get('choice_scores',{}))
    preds=[]; traces=[]
    for inst in instances:
        req=[(inst['context'], c) for c in inst['choices']]
        scores=lm.loglikelihood(req)
        best=max(range(len(scores)), key=lambda i:scores[i][0])
        preds.append(inst['choices'][best]); traces.append({'context':inst['context'],'scores':scores,'prediction':inst['choices'][best],'target':inst['target']})
    metrics=compute_metrics(preds,[i['target'] for i in instances], cfg['metric_list'])
    return {'predictions':preds,'metrics':metrics,'item_traces':traces,'sample_count':len(docs)}

def main():
    inp=Path(sys.argv[1]); out=Path(sys.argv[2])
    data=json.loads(inp.read_text())
    result=run_eval(data['task_config'], data['documents'])
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2)+'\n')
if __name__=='__main__': main()
