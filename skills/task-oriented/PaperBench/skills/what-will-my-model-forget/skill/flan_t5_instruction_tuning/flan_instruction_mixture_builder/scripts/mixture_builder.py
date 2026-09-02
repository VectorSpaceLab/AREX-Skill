import argparse, json
from collections import Counter

def normalize(value):
    return str(value or "").strip().lower().replace(" ", "_")

def build_mixture(tasks, heldout):
    heldout_norm = {normalize(item) for item in heldout}
    retained, excluded = [], []
    for task in tasks:
        task_id, benchmark = normalize(task.get("task_id")), normalize(task.get("benchmark"))
        if task_id in heldout_norm or benchmark in heldout_norm:
            excluded.append({"task_id": task.get("task_id"), "reason": "heldout_overlap"}); continue
        retained.append(dict(task))
    source_counts = Counter(task.get("source", "unknown") for task in retained)
    return {"mixture": retained, "audit": {"retained_task_ids": [task.get("task_id") for task in retained], "excluded": excluded, "source_counts": dict(sorted(source_counts.items())), "cot_task_count": sum(1 for task in retained if bool(task.get("cot"))), "heldout": sorted(heldout_norm)}}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--tasks", required=True); p.add_argument("--heldout", nargs="*", default=[]); p.add_argument("--output", required=True); a=p.parse_args()
    with open(a.tasks, encoding="utf-8") as h: tasks=json.load(h)
    with open(a.output,"w",encoding="utf-8") as h: json.dump(build_mixture(tasks,a.heldout),h,indent=2,sort_keys=True)
if __name__ == "__main__": main()
