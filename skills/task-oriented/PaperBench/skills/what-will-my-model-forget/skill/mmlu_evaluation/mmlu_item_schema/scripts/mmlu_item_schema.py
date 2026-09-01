import json, argparse
LABELS=("A","B","C","D")
def canonical_label(value):
    text=str(value).strip().upper()
    if text.startswith("(") and len(text)>1: text=text[1:2].upper()
    if text not in LABELS: raise ValueError(f"invalid answer label: {value}")
    return text
def validate_item(item):
    opts=item.get("choices") or item.get("options")
    if not isinstance(opts, dict) or set(opts)!={"A","B","C","D"}: raise ValueError("item must contain choices A-D")
    q=str(item.get("question","")).strip()
    subj=str(item.get("subject","")).strip()
    if not q or not subj: raise ValueError("subject and question are required")
    ans=canonical_label(item.get("answer"))
    return {"subject":subj,"question":q,"choices":{k:str(opts[k]).strip() for k in LABELS},"answer":ans}
def format_question(item, include_answer=False):
    it=validate_item(item)
    lines=[f"Question: {it['question']}"]+[f"{k}. {it['choices'][k]}" for k in LABELS]
    lines.append("Answer:"+(f" {it['answer']}" if include_answer else ""))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output',required=True); a=p.parse_args()
    data=json.loads(open(a.input).read()); out=validate_item(data); open(a.output,'w').write(json.dumps(out,indent=2)+"\n")
if __name__=='__main__': main()
