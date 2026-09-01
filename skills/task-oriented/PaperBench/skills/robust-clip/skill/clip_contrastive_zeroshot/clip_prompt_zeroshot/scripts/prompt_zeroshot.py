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

def softmax(values):
    maxv = max(values)
    exps = [math.exp(v - maxv) for v in values]
    denom = sum(exps)
    return [v / denom for v in exps]


def class_vectors(class_names, prompt_embeddings_by_class):
    vectors = {}
    for name in class_names:
        prompts = prompt_embeddings_by_class[name]
        normalized = [normalize(v) for v in prompts]
        avg = [sum(vec[i] for vec in normalized) / len(normalized) for i in range(len(normalized[0]))]
        vectors[name] = normalize(avg)
    return vectors


def classify(image_embeddings, class_names, prompt_embeddings_by_class, logit_scale=10.0):
    vectors = class_vectors(class_names, prompt_embeddings_by_class)
    ordered = [vectors[name] for name in class_names]
    outputs = []
    for image in image_embeddings:
        image_n = normalize(image)
        scores = [logit_scale * dot(image_n, text) for text in ordered]
        probs = softmax(scores)
        best = max(range(len(scores)), key=lambda i: scores[i])
        outputs.append({"scores": dict(zip(class_names, scores)), "probabilities": dict(zip(class_names, probs)), "prediction": class_names[best]})
    return outputs
