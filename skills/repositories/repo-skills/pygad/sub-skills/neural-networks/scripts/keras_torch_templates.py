#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path

import numpy as np

import pygad


def dependency_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def write_summary(summary: dict, prefix: str) -> None:
    with tempfile.TemporaryDirectory(prefix=prefix) as tmpdir:
        summary_path = Path(tmpdir) / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(f"wrote summary to {summary_path}")


def run_keras_template() -> dict:
    if not dependency_available("tensorflow"):
        raise SystemExit(
            "Keras template requires TensorFlow/Keras. Install pygad[deep_learning] or tensorflow, then rerun."
        )

    try:
        import tensorflow as tf
        import tensorflow.keras as keras
        import pygad.kerasga as kerasga
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Keras template could not import tensorflow.keras. Install TensorFlow/Keras, then rerun."
        ) from exc

    np.random.seed(21)
    tf.random.set_seed(21)

    x = np.array([[0.0, 0.0],
                  [0.0, 1.0],
                  [1.0, 0.0],
                  [1.0, 1.0]], dtype=np.float32)
    y = np.array([[1.0, 0.0],
                  [0.0, 1.0],
                  [0.0, 1.0],
                  [1.0, 0.0]], dtype=np.float32)

    inputs = keras.layers.Input(shape=(2,))
    hidden = keras.layers.Dense(4, activation="relu")(inputs)
    outputs = keras.layers.Dense(2, activation="softmax")(hidden)
    model = keras.Model(inputs=inputs, outputs=outputs)

    keras_ga = kerasga.KerasGA(model=model, num_solutions=4)
    loss_fn = keras.losses.CategoricalCrossentropy()

    def fitness_func(ga_instance, solution, sol_idx):
        predictions = kerasga.predict(model=model,
                                      solution=solution,
                                      data=x,
                                      verbose=0)
        loss = loss_fn(y, predictions).numpy()
        return 1.0 / (loss + 1e-8)

    ga_instance = pygad.GA(num_generations=2,
                           num_parents_mating=2,
                           initial_population=keras_ga.population_weights,
                           fitness_func=fitness_func,
                           suppress_warnings=True,
                           random_seed=21)
    ga_instance.run()
    best_solution, best_fitness, best_idx = ga_instance.best_solution()
    predictions = kerasga.predict(model=model,
                                  solution=best_solution,
                                  data=x,
                                  verbose=0)

    summary = {
        "backend": "keras",
        "best_fitness": float(best_fitness),
        "best_index": int(best_idx),
        "population_size": len(keras_ga.population_weights),
        "prediction_shape": list(predictions.shape),
    }
    write_summary(summary, prefix="pygad-keras-template-")
    return summary


def run_torch_template() -> dict:
    if not dependency_available("torch"):
        raise SystemExit(
            "Torch template requires PyTorch. Install pygad[deep_learning] or torch, then rerun."
        )

    try:
        import torch
        import pygad.torchga as torchga
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Torch template could not import torch. Install PyTorch, then rerun."
        ) from exc

    np.random.seed(21)
    torch.manual_seed(21)

    x = torch.tensor([[0.0, 0.0],
                      [0.1, 0.6],
                      [1.0, 0.0],
                      [1.1, 1.3]], dtype=torch.float32)
    y = torch.tensor([[1.0, 0.0],
                      [0.0, 1.0],
                      [0.0, 1.0],
                      [1.0, 0.0]], dtype=torch.float32)

    model = torch.nn.Sequential(
        torch.nn.Linear(2, 4),
        torch.nn.ReLU(),
        torch.nn.Linear(4, 2),
        torch.nn.Softmax(dim=1),
    )

    torch_ga = torchga.TorchGA(model=model, num_solutions=4)
    loss_fn = torch.nn.BCELoss()

    def fitness_func(ga_instance, solution, sol_idx):
        predictions = torchga.predict(model=model,
                                      solution=solution,
                                      data=x)
        loss = loss_fn(predictions, y).detach().cpu().numpy()
        return 1.0 / (loss + 1e-8)

    ga_instance = pygad.GA(num_generations=2,
                           num_parents_mating=2,
                           initial_population=torch_ga.population_weights,
                           fitness_func=fitness_func,
                           suppress_warnings=True,
                           random_seed=21)
    ga_instance.run()
    best_solution, best_fitness, best_idx = ga_instance.best_solution()
    predictions = torchga.predict(model=model,
                                  solution=best_solution,
                                  data=x)

    summary = {
        "backend": "torch",
        "best_fitness": float(best_fitness),
        "best_index": int(best_idx),
        "population_size": len(torch_ga.population_weights),
        "prediction_shape": list(predictions.shape),
    }
    write_summary(summary, prefix="pygad-torch-template-")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small PyGAD Keras or Torch template.")
    parser.add_argument(
        "--backend",
        choices=("auto", "keras", "torch"),
        default="auto",
        help="Which optional deep-learning backend to exercise.",
    )
    args = parser.parse_args()

    if args.backend == "keras":
        run_keras_template()
    elif args.backend == "torch":
        run_torch_template()
    else:
        if dependency_available("tensorflow"):
            run_keras_template()
        elif dependency_available("torch"):
            run_torch_template()
        else:
            raise SystemExit(
                "No optional deep-learning backend was found. Install TensorFlow/Keras or PyTorch, then rerun."
            )


if __name__ == "__main__":
    main()
