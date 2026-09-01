import argparse
import json
import math


def _norm(row):
    value = math.sqrt(sum(x * x for x in row))
    if value <= 0:
        raise ValueError("zero vector cannot be normalized")
    return [x / value for x in row]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross_entropy(logits):
    losses = []
    for index, row in enumerate(logits):
        maximum = max(row)
        exps = [math.exp(value - maximum) for value in row]
        denom = sum(exps)
        losses.append(-(row[index] - maximum) + math.log(denom))
    return sum(losses) / len(losses)


def compute_contrastive(image_embeddings, text_embeddings, logit_scale=10.0):
    if len(image_embeddings) != len(text_embeddings) or not image_embeddings:
        raise ValueError("image/text batches must be non-empty and aligned")
    if logit_scale <= 0:
        raise ValueError("logit_scale must be positive")
    width = len(image_embeddings[0])
    if width == 0 or any(len(row) != width for row in image_embeddings + text_embeddings):
        raise ValueError("all embeddings must share a non-empty dimension")
    image_norm = [_norm(row) for row in image_embeddings]
    text_norm = [_norm(row) for row in text_embeddings]
    logits = [[logit_scale * _dot(image, text) for text in text_norm] for image in image_norm]
    logits_t = [list(row) for row in zip(*logits)]
    loss = (_cross_entropy(logits) + _cross_entropy(logits_t)) / 2.0
    diagonal = [logits[i][i] for i in range(len(logits))]
    off_diag = [logits[i][j] for i in range(len(logits)) for j in range(len(logits)) if i != j]
    return {
        "schema_version": 1,
        "logits": logits,
        "loss": loss,
        "image_norms": [math.sqrt(sum(x*x for x in row)) for row in image_norm],
        "text_norms": [math.sqrt(sum(x*x for x in row)) for row in text_norm],
        "mean_diagonal_logit": sum(diagonal) / len(diagonal),
        "mean_off_diagonal_logit": sum(off_diag) / len(off_diag) if off_diag else 0.0,
        "diagonal_margin_positive": (sum(diagonal) / len(diagonal)) > (sum(off_diag) / len(off_diag) if off_diag else -1e9)
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = compute_contrastive(payload["image_embeddings"], payload["text_embeddings"], payload.get("logit_scale", 10.0))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

if __name__ == "__main__":
    main()
