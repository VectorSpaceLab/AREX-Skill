from collections import Counter, defaultdict


def make_split(records, heldout_dataset_ids=None, heldout_task_families=None):
    heldout_dataset_ids=set(heldout_dataset_ids or [])
    heldout_task_families=set(heldout_task_families or [])
    train=[]; eval=[]
    for r in records:
        if r.get('dataset_id') in heldout_dataset_ids or r.get('task_family') in heldout_task_families:
            eval.append(r)
        else:
            train.append(r)
    leaked=sorted({r['dataset_id'] for r in train} & heldout_dataset_ids)
    template_counts=defaultdict(Counter)
    for r in records:
        template_counts[r['dataset_id']][r['template_id']]+=1
    return {'train':train,'eval':eval,'diagnostics':{'train_count':len(train),'eval_count':len(eval),'heldout_dataset_ids':sorted(heldout_dataset_ids),'leaked_heldout_dataset_ids':leaked,'template_counts':{k:dict(v) for k,v in template_counts.items()}}}
