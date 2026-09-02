import json, argparse, sys
from pathlib import Path
_item_scripts = Path(__file__).resolve().parents[2] / "mmlu_item_schema" / "scripts"
if _item_scripts.exists():
    sys.path.insert(0, str(_item_scripts))
from mmlu_item_schema import validate_item, format_question
def build_prompt(subject, dev_items, test_item, shot_count=5):
    shots=[validate_item(x) for x in dev_items[:shot_count]]
    test=validate_item(test_item)
    header=f"The following are multiple choice questions (with answers) about {subject}."
    blocks=[header]+[format_question(x, include_answer=True) for x in shots]+[format_question(test, include_answer=False)]
    return "\n\n".join(blocks), {"subject":subject,"shot_count":len(shots),"test_answer_hidden":True}
def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output',required=True); a=p.parse_args()
    data=json.loads(open(a.input).read()); prompt,meta=build_prompt(data['subject'],data.get('dev_items',[]),data['test_item'],data.get('shot_count',5)); open(a.output,'w').write(json.dumps({"prompt":prompt,"metadata":meta},indent=2)+"\n")
if __name__=='__main__': main()
