#!/usr/bin/env python3
import math


def softmax(logits):
    max_logit = max(logits)
    exps = [math.exp(value - max_logit) for value in logits]
    total = sum(exps)
    return [value / total for value in exps]


def predict_probabilities(features, weights):
    probabilities = []
    for row in features:
        logits = []
        for class_weights in weights:
            logits.append(sum(feature * weight for feature, weight in zip(row, class_weights)))
        probabilities.append(softmax(logits))
    return probabilities


def cross_entropy_loss(features, labels, weights):
    probabilities = predict_probabilities(features, weights)
    total = 0.0
    for probs, label in zip(probabilities, labels):
        total -= math.log(max(probs[label], 1e-12))
    return total / len(labels)


def gradient_step(features, labels, weights, learning_rate=0.2):
    class_count = len(weights)
    feature_count = len(weights[0])
    gradients = [[0.0 for _ in range(feature_count)] for _ in range(class_count)]
    probabilities = predict_probabilities(features, weights)
    for row, label, probs in zip(features, labels, probabilities):
        for class_index in range(class_count):
            error = probs[class_index] - (1.0 if class_index == label else 0.0)
            for feature_index, feature in enumerate(row):
                gradients[class_index][feature_index] += error * feature / len(labels)
    updated = []
    for class_index in range(class_count):
        updated.append([
            weights[class_index][feature_index] - learning_rate * gradients[class_index][feature_index]
            for feature_index in range(feature_count)
        ])
    return updated


def make_proxy_dataset():
    return {
        "features": [
            [1.0, 0.1, 1.0],
            [0.9, -0.1, 1.0],
            [-1.0, -0.2, 1.0],
            [-0.8, 0.2, 1.0],
            [0.05, 0.9, 1.0],
            [-0.05, -0.9, 1.0],
        ],
        "labels": [0, 0, 1, 1, 0, 1],
        "description": "Six-example binary classification proxy with four easy margin examples and two near-boundary high-error examples.",
    }


def initial_weights():
    return [[0.25, 0.0, 0.0], [-0.25, 0.0, 0.0]]
