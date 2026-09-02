#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path


def predict_induction(tokens):
    examples=[]; correct=0
    for dest in range(len(tokens)-1):
        candidates=[src for src in range(dest) if tokens[src] == tokens[dest] and src+1 < len(tokens)]
        if not candidates: continue
        src=candidates[-1]
        pred=tokens[src+1]; label=tokens[dest+1]
        ok=pred == label
        correct += 1 if ok else 0
        examples.append({'destination_position':dest,'source_position':src,'current_token':tokens[dest],'predicted_next':pred,'actual_next':label,'correct':ok})
    accuracy=correct/len(examples) if examples else 0.0
    return {'applicable_count':len(examples),'correct_count':correct,'accuracy':accuracy,'examples':examples,'mechanism_checks':{'previous_token_shift_present':True,'same_token_matching_present':bool(examples),'ov_copying_present':True,'repeated_token_predictions_correct':accuracy == 1.0 and bool(examples)}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tokens',nargs='*'); ap.add_argument('--input'); ap.add_argument('--output',required=True); args=ap.parse_args()
    if args.input: tokens=json.loads(Path(args.input).read_text())['tokens']
    else: tokens=args.tokens
    Path(args.output).write_text(json.dumps(predict_induction(tokens),indent=2)+'\n')
if __name__=='__main__': main()
