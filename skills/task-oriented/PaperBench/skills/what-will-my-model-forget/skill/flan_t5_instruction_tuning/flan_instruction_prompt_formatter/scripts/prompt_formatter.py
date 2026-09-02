import argparse, json

def render_prompt(example):
    return f"Instruction: {example.get('instruction') or 'Answer the task.'}\nInput: {example.get('input') or ''}\nOutput:"

def hidden_answer_separated(prompt, answer):
    answer=str(answer or "").strip()
    lowered=prompt.lower()
    return f"output: {answer.lower()}" not in lowered and f"answer is {answer.lower()}" not in lowered

def format_example(example, mode="direct", exemplars=None):
    exemplars=exemplars or []; parts=[]
    if mode == "few_shot":
        for ex in exemplars: parts.append(f"Instruction: {ex.get('instruction','Answer the task.')}\nInput: {ex.get('input','')}\nOutput: {ex.get('answer','')}\n")
    parts.append(render_prompt(example)); prompt="\n".join(parts)
    answer=str(example.get("answer", "")); rationale=str(example.get("rationale", "")); cot_used=mode == "cot" and bool(rationale)
    completion=f"{rationale} Therefore, the answer is {answer}" if cot_used else answer
    return {"task_id": example.get("task_id"), "source": example.get("source"), "format_mode": mode, "prompt": prompt, "completion": completion, "metadata": {"exemplar_count": len(exemplars) if mode == "few_shot" else 0, "cot_used": cot_used, "answer_separated_from_prompt": hidden_answer_separated(prompt, answer)}}

def format_examples(examples, mode="direct", exemplars=None): return [format_example(ex, mode, exemplars) for ex in examples]

def main():
    p=argparse.ArgumentParser(); p.add_argument("--examples", required=True); p.add_argument("--mode", choices=["direct","few_shot","cot"], default="direct"); p.add_argument("--output", required=True); a=p.parse_args()
    with open(a.examples, encoding="utf-8") as h: examples=json.load(h)
    with open(a.output,"w",encoding="utf-8") as h: json.dump(format_examples(examples,a.mode),h,indent=2,sort_keys=True)
if __name__ == "__main__": main()
