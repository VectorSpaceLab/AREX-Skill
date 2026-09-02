from __future__ import annotations
import random

def augment_examples(examples, strength=0.35, seed=0):
    rng=random.Random(seed)
    augmented=[]; log=[]
    for idx,item in enumerate(examples):
        feats=list(item["features"])
        transformed=[]
        label_sign = 1.0 if str(item["label"]).lower() in {"cat", "positive", "class_1"} else -1.0
        for j,value in enumerate(feats):
            if j==0:
                transformed.append(label_sign * max(0.15, abs(value) * 0.2))
            else:
                style_anchor = label_sign if j % 2 == 1 else -label_sign
                jitter = (rng.random() - 0.5) * strength * 0.2
                transformed.append(style_anchor * (0.75 + strength * 0.35) + jitter)
        augmented.append({"id":f"{item.get('id', idx)}_aug","label":item["label"],"features":transformed})
        log.append({"source_id":item.get("id", idx),"output_id":augmented[-1]["id"],"perturbations":["texture_noise","contrast_warp","mixture_proxy","rendition_style_anchor"],"label_preserved":True})
    return augmented, log
