from __future__ import annotations
import math

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(v): return math.sqrt(sum(x*x for x in v))
def normalize(v):
    n = norm(v)
    if n <= 1e-12: raise ValueError("zero vector cannot be normalized")
    return [x/n for x in v]
def logits(image_embeddings, text_embeddings, scale=10.0):
    images=[normalize(v) for v in image_embeddings]
    texts=[normalize(v) for v in text_embeddings]
    return [[scale*dot(i,t) for t in texts] for i in images]
def logsumexp(values):
    m=max(values)
    return m+math.log(sum(math.exp(v-m) for v in values))
def cross_entropy_rows(matrix):
    total=0.0
    for i,row in enumerate(matrix):
        total += -row[i] + logsumexp(row)
    return total/len(matrix)
def transpose(matrix): return [list(row) for row in zip(*matrix)]
def symmetric_contrastive_loss(image_embeddings, text_embeddings, scale=10.0):
    if len(image_embeddings) != len(text_embeddings): raise ValueError("paired batches must have same length")
    matrix=logits(image_embeddings,text_embeddings,scale)
    return {"logits_per_image": matrix, "logits_per_text": transpose(matrix), "loss": 0.5*(cross_entropy_rows(matrix)+cross_entropy_rows(transpose(matrix)))}
def train_text_bias_proxy(image_embeddings, base_text_embeddings, labels, steps=8, lr=0.2, scale=5.0):
    biases=[[0.0 for _ in base_text_embeddings[0]] for _ in base_text_embeddings]
    trace=[]
    def shifted(): return [[x+b for x,b in zip(row,bias)] for row,bias in zip(base_text_embeddings,biases)]
    before=symmetric_contrastive_loss(image_embeddings, shifted(), scale)["loss"]
    for _ in range(steps):
        eps=1e-4
        for row in range(len(biases)):
            for col in range(len(biases[row])):
                old=biases[row][col]
                biases[row][col]=old+eps; plus=symmetric_contrastive_loss(image_embeddings, shifted(), scale)["loss"]
                biases[row][col]=old-eps; minus=symmetric_contrastive_loss(image_embeddings, shifted(), scale)["loss"]
                biases[row][col]=old-lr*((plus-minus)/(2*eps))
        trace.append(symmetric_contrastive_loss(image_embeddings, shifted(), scale)["loss"])
    after=symmetric_contrastive_loss(image_embeddings, shifted(), scale)["loss"]
    return {"loss_before": before, "loss_after": after, "params_before": [[0.0 for _ in base_text_embeddings[0]] for _ in base_text_embeddings], "params_after": biases, "loss_history": trace, "optimizer_state_changed": before != after}
