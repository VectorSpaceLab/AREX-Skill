#!/usr/bin/env python3
"""Print safe TorchDrug molecular workflow planning checklists.

This helper is intentionally offline: it does not import TorchDrug, download datasets,
create files, train models, or contact network resources. It prints minimal skeletons
that a user can adapt in their own runtime.
"""

from __future__ import annotations

import argparse
import textwrap


TEMPLATES = {
    "property": {
        "title": "Molecular property prediction",
        "checklist": [
            "Choose built-in or custom molecule dataset; confirm sample labels match task names.",
            "Select random split for tutorial parity or scaffold split for chemistry generalization.",
            "Match model input_dim to dataset.node_feature_dim and edge_input_dim to dataset.edge_feature_dim when bonds are used.",
            "Use PropertyPrediction with criterion='bce' for binary classification or 'mse' for regression.",
            "Wire optimizer and core.Engine only after dataset, splits, model, and task are finalized.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            dataset = datasets.ClinTox("molecule-datasets")
            lengths = [int(0.8 * len(dataset)), int(0.1 * len(dataset))]
            lengths.append(len(dataset) - sum(lengths))
            torch.manual_seed(1)
            train_set, valid_set, test_set = torch.utils.data.random_split(dataset, lengths)

            model = models.GIN(
                input_dim=dataset.node_feature_dim,
                hidden_dims=[256, 256, 256, 256],
                short_cut=True,
                batch_norm=True,
                concat_hidden=True,
            )
            task = tasks.PropertyPrediction(
                model,
                task=dataset.tasks,
                criterion="bce",
                metric=("auprc", "auroc"),
            )
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=128)
        """,
    },
    "pretrain": {
        "title": "Molecular pretraining and finetuning",
        "checklist": [
            "Use atom_feature='pretrain' and bond_feature='pretrain' for both pretraining and finetuning.",
            "Choose InfoGraph for graph-node mutual information or AttributeMasking for atom-type reconstruction.",
            "Keep the downstream base model architecture identical before loading pretrained weights.",
            "Load checkpoint['model'] with strict=False after wrapping the downstream PropertyPrediction task.",
            "Use scaffold split for downstream BACE-style finetuning when generalization matters.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            dataset = datasets.ClinTox("molecule-datasets", atom_feature="pretrain", bond_feature="pretrain")
            base = models.GIN(
                input_dim=dataset.node_feature_dim,
                hidden_dims=[300, 300, 300, 300, 300],
                edge_input_dim=dataset.edge_feature_dim,
                batch_norm=True,
                readout="mean",
            )
            # Option A: InfoGraph
            task = tasks.Unsupervised(models.InfoGraph(base, separate_model=False))
            # Option B: Attribute masking
            # task = tasks.AttributeMasking(base, mask_rate=0.15)
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, dataset, None, None, optimizer, gpus=None, batch_size=128)
        """,
    },
    "generation": {
        "title": "Molecule generation with GCPN or GraphAF",
        "checklist": [
            "Use ZINC250k with kekulize=True and atom_feature='symbol'.",
            "For GCPN, pass dataset.atom_types into GCPNGeneration.",
            "For GraphAF, create separate node and edge GraphAF flows; edge prior adds a non-edge class.",
            "Pretrain with criterion='nll' before PPO finetuning for qed or plogp.",
            "Treat generated score/SMILES output as candidates; inspect validity and diversity, not only top scores.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            dataset = datasets.ZINC250k("molecule-datasets", kekulize=True, atom_feature="symbol")
            model = models.RGCN(
                input_dim=dataset.node_feature_dim,
                num_relation=dataset.num_bond_type,
                hidden_dims=[256, 256, 256, 256],
                batch_norm=False,
            )
            task = tasks.GCPNGeneration(
                model,
                dataset.atom_types,
                max_edge_unroll=12,
                max_node=38,
                criterion="nll",
            )
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, dataset, None, None, optimizer, gpus=None, batch_size=32)
            # After training or loading: results = task.generate(num_sample=32, max_resample=5)
        """,
    },
    "retrosynthesis": {
        "title": "Retrosynthesis with G2Gs",
        "checklist": [
            "Create USPTO50k twice: reaction mode for center identification and as_synthon=True for synthon completion.",
            "Use atom_feature='center_identification' for reaction mode and 'synthon_completion' for synthon mode.",
            "Set the same torch.manual_seed immediately before each dataset.split() call.",
            "Train CenterIdentification and SynthonCompletion separately before wrapping Retrosynthesis.",
            "Tune center_topk, num_synthon_beam, and max_prediction for beam-search recall versus runtime.",
        ],
        "skeleton": """
            import torch
            from torchdrug import core, datasets, models, tasks

            reaction_dataset = datasets.USPTO50k(
                "molecule-datasets",
                atom_feature="center_identification",
                kekulize=True,
            )
            synthon_dataset = datasets.USPTO50k(
                "molecule-datasets",
                as_synthon=True,
                atom_feature="synthon_completion",
                kekulize=True,
            )
            torch.manual_seed(1)
            reaction_train, reaction_valid, reaction_test = reaction_dataset.split()
            torch.manual_seed(1)
            synthon_train, synthon_valid, synthon_test = synthon_dataset.split()

            reaction_model = models.RGCN(
                input_dim=reaction_dataset.node_feature_dim,
                hidden_dims=[256, 256, 256, 256, 256, 256],
                num_relation=reaction_dataset.num_bond_type,
                concat_hidden=True,
            )
            reaction_task = tasks.CenterIdentification(reaction_model, feature=("graph", "atom", "bond"))
            synthon_model = models.RGCN(
                input_dim=synthon_dataset.node_feature_dim,
                hidden_dims=[256, 256, 256, 256, 256, 256],
                num_relation=synthon_dataset.num_bond_type,
                concat_hidden=True,
            )
            synthon_task = tasks.SynthonCompletion(synthon_model, feature=("graph",))
            task = tasks.Retrosynthesis(reaction_task, synthon_task, center_topk=2, num_synthon_beam=5, max_prediction=10)
            optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
            solver = core.Engine(task, reaction_train, reaction_valid, reaction_test, optimizer, gpus=None, batch_size=16)
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
        description="Print a safe TorchDrug molecular workflow checklist and minimal API skeleton.",
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
