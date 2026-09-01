import json
from typing import Iterable, List, Optional, Sequence


def build_prefix_examples(sequences: Sequence[Sequence[str]], mode: str, labels: Optional[Sequence[int]] = None, target: Optional[str] = None):
    if mode not in {"whole_sequence", "future_suffix"}:
        raise ValueError("mode must be whole_sequence or future_suffix")
    if mode == "whole_sequence" and labels is None:
        raise ValueError("labels are required for whole_sequence mode")
    if mode == "future_suffix" and target is None:
        raise ValueError("target is required for future_suffix mode")
    examples=[]; empty=0
    for sid, seq in enumerate(sequences):
        seq=list(seq)
        if not seq:
            empty += 1; continue
        for pos in range(1, len(seq)+1):
            prefix=seq[:pos]
            if mode == "whole_sequence":
                label=int(labels[sid])
            else:
                label=int(target in seq[pos-1:])
            examples.append({"source_sequence_id": sid, "position": pos, "prefix_tokens": prefix, "label": label, "target": target if target is not None else "attribute"})
    return {"examples": examples, "metadata": {"mode": mode, "sequence_count": len(sequences), "empty_sequences": empty}}


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--sequences-json', required=True)
    p.add_argument('--mode', required=True)
    p.add_argument('--labels-json', default='')
    p.add_argument('--target', default=None)
    p.add_argument('--output', required=True)
    a=p.parse_args()
    sequences=json.loads(a.sequences_json)
    labels=json.loads(a.labels_json) if a.labels_json else None
    out=build_prefix_examples(sequences, a.mode, labels, a.target)
    open(a.output,'w').write(json.dumps(out,indent=2)+"\n")
if __name__ == '__main__': main()
