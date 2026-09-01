from __future__ import annotations
import math

def normalize(v):
    n=math.sqrt(sum(x*x for x in v))
    if n <= 1e-12: raise ValueError("zero vector cannot be normalized")
    return [x/n for x in v]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def render_prompts(class_names, templates):
    if not class_names: raise ValueError("class_names must be non-empty")
    if not templates or any("{label}" not in t for t in templates): raise ValueError("templates must contain {label}")
    return {name:[t.format(label=name) for t in templates] for name in class_names}
def build_class_prototypes(class_names, text_features_by_class):
    prototypes=[]
    for name in class_names:
        feats=text_features_by_class[name]
        dim=len(feats[0])
        avg=[sum(row[i] for row in feats)/len(feats) for i in range(dim)]
        prototypes.append(normalize(avg))
    return prototypes
def classify(image_embeddings, class_names, text_features_by_class, scale=10.0):
    prototypes=build_class_prototypes(class_names,text_features_by_class)
    logits=[[scale*dot(normalize(img), proto) for proto in prototypes] for img in image_embeddings]
    predictions=[class_names[max(range(len(row)), key=lambda i: row[i])] for row in logits]
    return {"prototypes": prototypes, "logits": logits, "predictions": predictions}
def accuracy(predictions, labels):
    return sum(p==y for p,y in zip(predictions, labels))/len(labels)
