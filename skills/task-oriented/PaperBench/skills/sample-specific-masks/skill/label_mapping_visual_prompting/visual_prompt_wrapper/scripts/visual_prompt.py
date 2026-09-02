from __future__ import annotations
import hashlib, json
from typing import Iterable, List, Optional

def fingerprint_model(weights: List[List[float]], bias: List[float]) -> str:
    return hashlib.sha256(json.dumps({'w':weights,'b':bias}, sort_keys=True).encode()).hexdigest()

def apply_prompt(x: Iterable[float], prompt: Iterable[float], mask: Optional[Iterable[float]]=None) -> List[float]:
    xv=list(map(float,x)); pv=list(map(float,prompt))
    if len(xv)!=len(pv): raise ValueError('prompt and input must have the same length')
    if mask is None: mv=[1.0]*len(xv)
    else:
        mv=list(map(float,mask))
        if len(mv)!=len(xv): raise ValueError('mask and input must have the same length')
    return [a+m*b for a,b,m in zip(xv,pv,mv)]

def linear_logits(x: Iterable[float], weights: List[List[float]], bias: List[float]) -> List[float]:
    xv=list(map(float,x))
    return [sum(wi*xi for wi,xi in zip(row,xv))+float(b) for row,b in zip(weights,bias)]

def run_frozen_linear_batch(xs, prompt, weights, bias, mask=None):
    before=fingerprint_model(weights,bias)
    prompted=[apply_prompt(x,prompt,mask) for x in xs]
    logits=[linear_logits(x,weights,bias) for x in prompted]
    preds=[max(range(len(row)), key=lambda i: row[i]) for row in logits]
    after=fingerprint_model(weights,bias)
    return {'prompted_inputs':prompted,'logits':logits,'predictions':preds,'frozen_source_unchanged': before==after,'fingerprint_before':before,'fingerprint_after':after}
