#!/usr/bin/env python3
"""Print a safe TorchDrug knowledge graph reasoning API skeleton.

This helper is intentionally side-effect free: it does not import TorchDrug,
download datasets, allocate accelerators, or train models. It only renders a
starter script for either an embedding-model or NeuralLP workflow.
"""

import argparse
import textwrap


DATASET_CHOICES = ["FB15k", "FB15k237", "WN18", "WN18RR", "YAGO310", "Hetionet"]
EMBEDDING_MODELS = ["TransE", "DistMult", "ComplEx", "RotatE", "SimplE", "KBGAT"]


def build_embedding_model(model):
    if model == "KBGAT":
        return """
model = models.KBGAT(
    num_entity=dataset.num_entity,
    num_relation=dataset.num_relation,
    embedding_dim=512,
    hidden_dims=[512, 512],
    max_score=12,
)""".strip()
    if model in {"DistMult", "ComplEx", "SimplE"}:
        return f"""
model = models.{model}(
    num_entity=dataset.num_entity,
    num_relation=dataset.num_relation,
    embedding_dim=512,
    l3_regularization=0,
)""".strip()

    embedding_dim = 2048 if model == "RotatE" else 512
    max_score = 9 if model == "RotatE" else 12
    return f"""
model = models.{model}(
    num_entity=dataset.num_entity,
    num_relation=dataset.num_relation,
    embedding_dim={embedding_dim},
    max_score={max_score},
)""".strip()


def build_embedding(dataset, model):
    model_block = build_embedding_model(model)
    return f"""
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.{dataset}("~/kg-datasets/")
train_set, valid_set, test_set = dataset.split()
{model_block}
task = tasks.KnowledgeGraphCompletion(
    model,
    criterion="bce",
    metric=("mr", "mrr", "hits@1", "hits@3", "hits@10"),
    num_negative=256,
    adversarial_temperature=1,
    strict_negative=True,
    filtered_ranking=True,
    full_batch_eval=False,
)
optimizer = torch.optim.Adam(task.parameters(), lr=2e-5)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=[0], batch_size=1024)
solver.train(num_epoch=200)
solver.evaluate("valid")
""".strip()


def build_neurallp(dataset):
    return f"""
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.{dataset}("~/kg-datasets/")
train_set, valid_set, test_set = dataset.split()
model = models.NeuralLP(
    num_relation=dataset.num_relation,
    hidden_dim=128,
    num_step=3,
    num_lstm_layer=2,
)
task = tasks.KnowledgeGraphCompletion(
    model,
    criterion="bce",
    metric=("mr", "mrr", "hits@1", "hits@3", "hits@10"),
    fact_ratio=0.75,
    num_negative=256,
    sample_weight=False,
    strict_negative=True,
    filtered_ranking=True,
    full_batch_eval=False,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1.0e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=[0], batch_size=64)
solver.train(num_epoch=10)
solver.evaluate("valid")
""".strip()


def main():
    parser = argparse.ArgumentParser(description="Print a TorchDrug KG reasoning skeleton without side effects.")
    parser.add_argument("--workflow", choices=["embedding", "neurallp"], default="embedding")
    parser.add_argument("--dataset", choices=DATASET_CHOICES, default="FB15k237")
    parser.add_argument("--model", choices=EMBEDDING_MODELS, default="RotatE")
    args = parser.parse_args()

    if args.workflow == "neurallp":
        skeleton = build_neurallp(args.dataset)
    else:
        skeleton = build_embedding(args.dataset, args.model)

    print(textwrap.dedent(skeleton).strip())


if __name__ == "__main__":
    main()
