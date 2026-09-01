from __future__ import annotations
import argparse, json, re

def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def encode_instruction(item, mode="full", include_negative=True):
    fields=item.get("instruction", item)
    instance=_clean(item.get("input", fields.get("input", "")))
    target=_clean(item.get("output", item.get("target", "")))
    parts=[]; used=[]
    if mode == "none":
        parts.append(f"Input: {instance}")
        parts.append("Output:")
        return {"text":"\n".join(parts), "fields_used":["input"], "target_leaked": target in "\n".join(parts) if target else False}
    if _clean(fields.get("prompt")):
        parts.append("Prompt: "+_clean(fields.get("prompt"))); used.append("prompt")
    if mode in {"full","prompt_definition","definition_examples"} and _clean(fields.get("definition")):
        parts.append("Definition: "+_clean(fields.get("definition"))); used.append("definition")
    if mode == "full" and _clean(fields.get("things_to_avoid")):
        parts.append("Things to Avoid: "+_clean(fields.get("things_to_avoid"))); used.append("things_to_avoid")
    if mode == "full" and _clean(fields.get("emphasis")):
        parts.append("Emphasis and Caution: "+_clean(fields.get("emphasis"))); used.append("emphasis")
    examples=[]
    if mode in {"full","positive_examples","definition_examples"}:
        examples.extend(("PositiveExample", ex) for ex in fields.get("positive_examples", []))
    if mode == "full" and include_negative:
        examples.extend(("NegativeExample", ex) for ex in fields.get("negative_examples", []))
    for idx,(kind,ex) in enumerate(examples,1):
        parts.append(f"{kind}{idx}: input: {_clean(ex.get('input'))}; output: {_clean(ex.get('output'))}; reason: {_clean(ex.get('reason'))}")
        used.append(kind.lower())
    parts.append("Input: "+instance)
    parts.append("Output:")
    text="\n".join(parts)
    return {"text":text, "fields_used":used+["input"], "target_leaked": bool(target and target in text)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input_json'); ap.add_argument('--mode', default='full'); ap.add_argument('--output', default='')
    ns=ap.parse_args(); data=json.load(open(ns.input_json, encoding='utf-8'))
    out=encode_instruction(data, ns.mode)
    if ns.output: json.dump(out, open(ns.output,'w',encoding='utf-8'), indent=2)
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
