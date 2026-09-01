import math

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def norm(v):
    return math.sqrt(sum(x * x for x in v))

def normalize(v):
    n = norm(v)
    if n == 0:
        raise ValueError("zero-norm embedding is invalid")
    return [x / n for x in v]

def logits(image_embeddings, text_embeddings, logit_scale=10.0):
    if len(image_embeddings) != len(text_embeddings) or not image_embeddings:
        raise ValueError("paired non-empty batches are required")
    images = [normalize(v) for v in image_embeddings]
    texts = [normalize(v) for v in text_embeddings]
    return [[logit_scale * dot(i, t) for t in texts] for i in images]


def _ce_rows(matrix):
    losses = []
    correct = 0
    for idx, row in enumerate(matrix):
        maxv = max(row)
        exps = [math.exp(v - maxv) for v in row]
        denom = sum(exps)
        losses.append(-(row[idx] - maxv - math.log(denom)))
        if max(range(len(row)), key=lambda j: row[j]) == idx:
            correct += 1
    return sum(losses) / len(losses), correct / len(matrix)


def symmetric_contrastive(image_embeddings, text_embeddings, logit_scale=10.0):
    matrix = logits(image_embeddings, text_embeddings, logit_scale)
    loss_i, acc_i = _ce_rows(matrix)
    transposed = [list(col) for col in zip(*matrix)]
    loss_t, acc_t = _ce_rows(transposed)
    return {"logits": matrix, "image_to_text_loss": loss_i, "text_to_image_loss": loss_t, "loss": (loss_i + loss_t) / 2, "retrieval_accuracy": (acc_i + acc_t) / 2}
