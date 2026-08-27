#!/usr/bin/env python3
"""Deploy a SchNetPack model as TorchScript for the LAMMPS pair style.

This is a self-contained adaptation of SchNetPack's ``spkdeploy`` helper. It is
intended for SchNetPack atomistic models that predict forces through response
modules, which is the model style expected by the SchNetPack LAMMPS interface.
"""

import argparse


def get_jit_model(model):
    """Return a TorchScript model compatible with SchNetPack's LAMMPS interface."""
    import torch
    import torch.nn as nn
    from schnetpack.transform import AddOffsets, CastTo32, CastTo64

    jit_postprocessors = nn.ModuleList()
    for postprocessor in model.postprocessors:
        if type(postprocessor) in [CastTo64, CastTo32]:
            continue
        if type(postprocessor) == AddOffsets:
            postprocessor.mean = postprocessor.mean.float()

        jit_postprocessors.append(postprocessor)
    model.postprocessors = jit_postprocessors

    return torch.jit.script(model)


def save_jit_model(model, model_path):
    """Script and save a SchNetPack model with cutoff metadata for LAMMPS."""
    import torch

    jit_model = get_jit_model(model)

    metadata = {}
    metadata["cutoff"] = str(jit_model.representation.cutoff.item()).encode("ascii")

    torch.jit.save(jit_model, model_path, _extra_files=metadata)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Deploy a trained SchNetPack response-module force model as "
            "TorchScript for the SchNetPack LAMMPS pair style. The saved model "
            "contains cutoff metadata read from model.representation.cutoff."
        )
    )
    parser.add_argument(
        "model_path",
        help=(
            "Path to the trained SchNetPack Python model, commonly a best_model "
            "checkpoint/load_model artifact. The model must expose postprocessors "
            "and representation.cutoff."
        ),
    )
    parser.add_argument(
        "deployed_model_path",
        help="Output path for the TorchScript model consumed by pair_style schnetpack.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help=(
            "Device used only while loading/scripting the model. Defaults to cpu; "
            "use cuda only when a compatible CUDA PyTorch stack is available."
        ),
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    import torch

    model = torch.load(args.model_path, map_location=args.device, weights_only=False)
    save_jit_model(model, args.deployed_model_path)

    print(f"stored deployed model at {args.deployed_model_path}.")
    print(
        "Use this deployed model in LAMMPS with pair_style schnetpack and a "
        "pair_coeff atom-type-to-atomic-number mapping."
    )


if __name__ == "__main__":
    main()
