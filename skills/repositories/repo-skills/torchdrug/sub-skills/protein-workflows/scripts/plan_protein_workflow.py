#!/usr/bin/env python3
"""Print safe TorchDrug protein workflow planning checklists.

This helper is intentionally offline: it does not import TorchDrug, download
datasets or model weights, allocate accelerators, create files, or train models.
It prints minimal skeletons that a user can adapt in their own runtime.
"""

from __future__ import annotations

import argparse
import textwrap


TEMPLATES = {
    "contact": {
        "title": "Protein contact prediction",
        "checklist": [
            "Use ProteinNet or a custom dataset that attaches graph.residue_position and graph.mask.",
            "Start with residue-only construction: atom_feature=None, bond_feature=None, residue_feature='default'.",
            "Choose a model that returns residue_feature, such as ProteinCNN, ProteinResNet, ProteinLSTM, ProteinBERT, or ESM.",
            "Set max_length small for CPU prototypes; pairwise scoring scales as batch_size * max_length ** 2.",
            "Use random_truncate=False for deterministic smoke tests, then enable random truncation for training augmentation if desired.",
            "Record threshold and gap because they define the contact labels and evaluated residue-pair mask.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            dataset = datasets.ProteinNet(
                "protein-datasets",
                atom_feature=None,
                bond_feature=None,
                residue_feature="default",
                lazy=True,
                verbose=1,
            )
            train_set, valid_set, test_set = dataset.split()
            model = models.ProteinCNN(
                input_dim=dataset.residue_feature_dim,
                hidden_dims=[64, 64],
                kernel_size=3,
                padding=1,
                readout="mean",
            )
            task = tasks.ContactPrediction(
                model,
                max_length=128,
                random_truncate=False,
                threshold=8.0,
                gap=6,
                metric=("accuracy", "prec@L5"),
            )
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=1)
        """,
    },
    "property": {
        "title": "Protein property or function prediction",
        "checklist": [
            "Pick the dataset family: regression, binary/multi-label function, multiclass localization, or custom labels.",
            "Match criterion and metrics to labels: mse for regression, bce for binary/multi-label, ce for integer multiclass.",
            "For sequence-only models, use residue_feature_dim as input_dim and residue-only protein construction.",
            "For structure-aware GearNet workflows, build a graph_construction_model and verify num_relation from selected edge layers.",
            "Use dataset.tasks when available; for custom datasets ensure sample keys exactly match the task names.",
            "Wire Engine only after dataset splits, model dimensions, and task target names are confirmed.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            dataset = datasets.Fluorescence(
                "protein-datasets",
                atom_feature=None,
                bond_feature=None,
                residue_feature="default",
                lazy=True,
                verbose=1,
            )
            train_set, valid_set, test_set = dataset.split()
            model = models.ProteinResNet(
                input_dim=dataset.residue_feature_dim,
                hidden_dims=[128, 128, 128],
                short_cut=True,
                layer_norm=True,
                readout="attention",
            )
            task = tasks.PropertyPrediction(
                model,
                task=dataset.tasks,
                criterion="mse",
                metric=("mae", "rmse", "spearmanr"),
                num_mlp_layer=2,
            )
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=16)
        """,
    },
    "interaction": {
        "title": "Protein-protein interaction or affinity prediction",
        "checklist": [
            "Use HumanPPI or YeastPPI for binary interaction labels, and PPIAffinity for regression affinity.",
            "Confirm samples contain graph1, graph2, and a target field such as interaction.",
            "Use tied weights by leaving model2=None unless the two protein sides need different encoders.",
            "Set criterion='bce' for binary PPI and criterion='mse' for affinity regression.",
            "Apply truncation or view transforms to both graph1 and graph2 when using pair datasets.",
            "Choose split keys deliberately if cross_species_test is present.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            dataset = datasets.HumanPPI(
                "protein-datasets",
                atom_feature=None,
                bond_feature=None,
                residue_feature="default",
                lazy=True,
                verbose=1,
            )
            train_set, valid_set, test_set = dataset.split(keys=["train", "valid", "test"])
            model = models.ProteinCNN(
                input_dim=dataset.residue_feature_dim,
                hidden_dims=[128, 128],
                readout="mean",
            )
            task = tasks.InteractionPrediction(
                model,
                task=dataset.tasks,
                criterion="bce",
                metric=("auprc", "auroc"),
                num_mlp_layer=2,
            )
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=8)
        """,
    },
}


def render(workflow: str) -> str:
    template = TEMPLATES[workflow]
    lines = [template["title"], "=" * len(template["title"]), "", "Checklist:"]
    lines.extend(f"- {item}" for item in template["checklist"])
    lines.extend(["", "Minimal API skeleton:", "", textwrap.dedent(template["skeleton"]).strip(), ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe TorchDrug protein workflow checklist and minimal API skeleton.",
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=sorted(TEMPLATES),
        help="Workflow family to plan. Prints only; does not download data or train.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(render(args.workflow))


if __name__ == "__main__":
    main()
