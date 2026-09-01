from __future__ import annotations
import argparse, json, random

def make_split(records, split_type='leave_one_task', holdout=None, seed=0, unseen_per_category=1):
    tasks={r['task_id']: r for r in records}
    if split_type == 'leave_one_task':
        unseen={holdout or sorted(tasks)[-1]}
    elif split_type == 'leave_one_category':
        unseen={r['task_id'] for r in records if r.get('category') == holdout}
    elif split_type == 'leave_one_dataset':
        unseen={r['task_id'] for r in records if r.get('dataset') == holdout}
    elif split_type == 'random_task':
        rng=random.Random(seed); by_cat={}
        for r in records: by_cat.setdefault(r.get('category','unknown'), []).append(r['task_id'])
        unseen=set()
        for ids in by_cat.values():
            ids=sorted(set(ids)); rng.shuffle(ids); unseen.update(ids[:unseen_per_category])
    else:
        raise ValueError('unknown split_type')
    if not unseen: raise ValueError('split produced no unseen tasks')
    seen=set(tasks)-unseen
    leakage=sorted(seen & unseen)
    return {'split_type':split_type,'seen_tasks':sorted(seen),'unseen_tasks':sorted(unseen),'leakage':leakage,'ok':not leakage and bool(seen)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('records_json'); ap.add_argument('--split-type',default='leave_one_task'); ap.add_argument('--holdout',default=None); ap.add_argument('--output',default='')
    ns=ap.parse_args(); records=json.load(open(ns.records_json, encoding='utf-8'))
    out=make_split(records, ns.split_type, ns.holdout)
    if ns.output: json.dump(out, open(ns.output,'w',encoding='utf-8'), indent=2)
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
