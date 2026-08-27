#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

import pygad.cnn as cnn
import pygad.gann as gann
import pygad.gacnn as gacnn
import pygad.nn as nn


def matrices_close(expected, actual):
    if len(expected) != len(actual):
        return False
    for left, right in zip(expected, actual):
        if not np.allclose(left, right):
            return False
    return True


def dense_smoke():
    np.random.seed(11)
    x = np.array([[0.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 0.0],
                  [1.0, 1.0]], dtype=float)
    y = np.array([0, 1, 1, 0])

    input_layer = nn.InputLayer(num_inputs=2)
    hidden_layer = nn.DenseLayer(num_neurons=3,
                                 previous_layer=input_layer,
                                 activation_function="relu")
    output_layer = nn.DenseLayer(num_neurons=2,
                                 previous_layer=hidden_layer,
                                 activation_function="softmax")

    initial_matrices = nn.layers_weights(output_layer, initial=True)
    initial_vector = nn.layers_weights_as_vector(output_layer, initial=True)
    restored_matrices = nn.layers_weights_as_matrix(output_layer, initial_vector.copy())
    assert matrices_close(initial_matrices, restored_matrices)

    nn.train(num_epochs=1,
             last_layer=output_layer,
             data_inputs=x,
             data_outputs=y,
             problem_type="classification",
             learning_rate=0.01)

    predictions = nn.predict(output_layer, x)
    assert len(predictions) == len(y)

    return {
        "vector_length": int(initial_vector.size),
        "predictions": [int(value) for value in predictions],
        "round_trip": True,
    }


def gann_smoke():
    np.random.seed(12)
    x = np.array([[0.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 0.0],
                  [1.0, 1.0]], dtype=float)

    gann_model = gann.GANN(num_solutions=3,
                           num_neurons_input=2,
                           num_neurons_output=2,
                           num_neurons_hidden_layers=[2],
                           hidden_activations="relu",
                           output_activation="softmax")

    population_vectors = gann.population_as_vectors(gann_model.population_networks)
    population_matrices = gann.population_as_matrices(gann_model.population_networks,
                                                      population_vectors)
    gann_model.update_population_trained_weights(population_trained_weights=population_matrices)

    predictions = nn.predict(gann_model.population_networks[0], x)
    assert len(predictions) == len(x)

    return {
        "population_size": len(population_vectors),
        "first_vector_length": int(population_vectors[0].size),
        "predictions": [int(value) for value in predictions],
    }


def build_cnn_model(seed):
    np.random.seed(seed)
    input_layer = cnn.Input2D(input_shape=(5, 5, 1))
    conv_layer = cnn.Conv2D(num_filters=2,
                            kernel_size=3,
                            previous_layer=input_layer,
                            activation_function=None)
    relu_layer = cnn.ReLU(previous_layer=conv_layer)
    pool_layer = cnn.MaxPooling2D(pool_size=2,
                                  previous_layer=relu_layer,
                                  stride=1)
    flatten_layer = cnn.Flatten(previous_layer=pool_layer)
    dense_layer = cnn.Dense(num_neurons=2,
                            previous_layer=flatten_layer,
                            activation_function="softmax")
    return cnn.Model(last_layer=dense_layer,
                     epochs=1,
                     learning_rate=0.01)


def cnn_smoke():
    model = build_cnn_model(seed=13)
    x = np.linspace(0.0, 1.0, num=2 * 5 * 5, dtype=float).reshape(2, 5, 5, 1)
    y = np.array([0, 1])

    initial_weights = cnn.layers_weights(model, initial=True)
    initial_vector = cnn.layers_weights_as_vector(model, initial=True)
    restored_weights = cnn.layers_weights_as_matrix(model, initial_vector.copy())
    assert matrices_close(initial_weights, restored_weights)

    model.train(train_inputs=x, train_outputs=y)
    predictions = model.predict(data_inputs=x)
    assert len(predictions) == len(y)

    return {
        "vector_length": int(initial_vector.size),
        "predictions": [int(value) for value in predictions],
    }


def gacnn_smoke():
    model = build_cnn_model(seed=14)
    x = np.linspace(0.0, 1.0, num=2 * 5 * 5, dtype=float).reshape(2, 5, 5, 1)

    gacnn_model = gacnn.GACNN(model=model,
                              num_solutions=2)

    population_vectors = gacnn.population_as_vectors(gacnn_model.population_networks)
    population_matrices = gacnn.population_as_matrices(gacnn_model.population_networks,
                                                       population_vectors)
    gacnn_model.update_population_trained_weights(population_trained_weights=population_matrices)

    predictions = gacnn_model.population_networks[0].predict(data_inputs=x)
    assert len(predictions) == len(x)

    return {
        "population_size": len(population_vectors),
        "first_vector_length": int(population_vectors[0].size),
        "predictions": [int(value) for value in predictions],
    }


def main():
    summary = {
        "dense": dense_smoke(),
        "gann": gann_smoke(),
        "cnn": cnn_smoke(),
        "gacnn": gacnn_smoke(),
    }

    with tempfile.TemporaryDirectory(prefix="pygad-neural-smoke-") as tmpdir:
        summary_path = Path(tmpdir) / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(f"wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
