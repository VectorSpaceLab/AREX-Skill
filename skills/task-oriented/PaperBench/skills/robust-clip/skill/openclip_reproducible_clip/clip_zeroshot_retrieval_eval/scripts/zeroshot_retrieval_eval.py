import argparse
import json
import math


def _norm(row):
    value = math.sqrt(sum(x*x for x in row))
    if value <= 0:
        raise ValueError("zero vector")
    return [x/value for x in row]


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _rank(scores):
    return sorted(range(len(scores)), key=lambda idx: (-scores[idx], idx))


def evaluate_clip_embeddings(image_embeddings, class_embeddings, labels, text_embeddings=None, recall_ks=(1, 5)):
    images = [_norm(row) for row in image_embeddings]
    classes = [_norm(row) for row in class_embeddings]
    if len(labels) != len(images):
        raise ValueError("labels must match image count")
    predictions = []
    correct = 0
    for image, label in zip(images, labels):
        scores = [_dot(image, klass) for klass in classes]
        pred = _rank(scores)[0]
        predictions.append(pred)
        if pred == label:
            correct += 1
    result = {"schema_version": 1, "top1_accuracy": 100.0 * correct / len(images), "predictions": predictions}
    if text_embeddings is not None:
        texts = [_norm(row) for row in text_embeddings]
        if len(texts) != len(images):
            raise ValueError("retrieval text count must match image count")
        similarity = [[_dot(image, text) for text in texts] for image in images]
        recalls = {}
        ranks = []
        for k in recall_ks:
            hits = 0
            for index, row in enumerate(similarity):
                ranking = _rank(row)
                if k == recall_ks[0]:
                    ranks.append(ranking)
                if index in ranking[:k]:
                    hits += 1
            recalls[f"image_to_text_recall_at_{k}"] = 100.0 * hits / len(images)
        result["retrieval"] = recalls
        result["image_to_text_rankings"] = ranks
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = evaluate_clip_embeddings(payload["image_embeddings"], payload["class_embeddings"], payload["labels"], payload.get("text_embeddings"), tuple(payload.get("recall_ks", [1, 5])))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

if __name__ == "__main__":
    main()
