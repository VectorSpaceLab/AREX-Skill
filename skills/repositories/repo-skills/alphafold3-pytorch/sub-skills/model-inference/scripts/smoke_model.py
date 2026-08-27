#!/usr/bin/env python3
"""Safe, bounded model contract probe for alphafold3-pytorch.

The default mode only inspects signatures. ``--mode forward`` constructs an
explicitly tiny model and samples one synthetic two-token input. It never
loads checkpoints, downloads optional encoder weights, trains, launches a
server, or writes files.
"""

from __future__ import annotations

import argparse
import inspect
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect model signatures or run one deliberately tiny synthetic forward."
    )
    parser.add_argument(
        "--mode",
        choices=("signature", "forward"),
        default="signature",
        help="signature inspection (default) or bounded synthetic sampling",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="execution device; CUDA must already be available (default: cpu)",
    )
    parser.add_argument(
        "--num-sample-steps",
        type=int,
        default=2,
        metavar="N",
        help="tiny EDM sample steps for --mode forward (2-4 recommended)",
    )
    parser.add_argument(
        "--with-confidence",
        action="store_true",
        help="also request and validate confidence-head logits",
    )
    parser.add_argument(
        "--with-distogram",
        action="store_true",
        help="also request distogram logits (implies --with-confidence)",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="random seed for the synthetic case"
    )
    parser.add_argument(
        "--debug", action="store_true", help="include the Python traceback on failure"
    )
    return parser.parse_args()


def resolve_device(name: str):
    import torch

    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested but torch.cuda.is_available() is false; rerun with --device cpu "
            "or make an already-installed CUDA runtime visible."
        )
    return torch.device(name)


def signature_check() -> int:
    try:
        from alphafold3_pytorch import Alphafold3, Alphafold3WithHubMixin
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "Could not import alphafold3_pytorch. Install the package and its required "
            "dependencies before using this probe; no dependency installation is attempted."
        ) from exc

    print("Alphafold3:", inspect.signature(Alphafold3))
    print("Alphafold3.forward:", inspect.signature(Alphafold3.forward))
    print("Alphafold3.forward_with_alphafold3_inputs:", inspect.signature(Alphafold3.forward_with_alphafold3_inputs))
    print("Alphafold3.init_and_load:", inspect.signature(Alphafold3.init_and_load))
    print("Alphafold3WithHubMixin:", inspect.signature(Alphafold3WithHubMixin))
    print("signature check: OK (no model constructed; no weights requested)")
    return 0


def build_tiny_model():
    """Construct only a deliberately tiny, no-optional-encoder model."""
    from alphafold3_pytorch import Alphafold3
    import torch

    bins = torch.linspace(2.0, 22.0, 8).tolist()
    error_bins = torch.linspace(0.5, 8.0, 8).tolist()
    return Alphafold3(
        dim_atom_inputs=3,
        dim_template_feats=4,
        dim_atom=8,
        dim_atompair_inputs=5,
        dim_atompair=4,
        dim_input_embedder_token=8,
        dim_single=8,
        dim_pairwise=8,
        dim_token=8,
        dim_msa_inputs=32,
        dim_additional_msa_feats=2,
        dim_additional_token_feats=33,
        num_molecule_mods=0,
        distance_bins=bins,
        pae_bins=error_bins,
        pde_bins=error_bins,
        num_dist_bins=len(bins),
        num_plddt_bins=4,
        diffusion_num_augmentations=1,
        num_rollout_steps=1,
        confidence_head_kwargs={"pairformer_depth": 1},
        template_embedder_kwargs={"pairformer_stack_depth": 1},
        msa_module_kwargs={
            "depth": 1,
            "dim_msa": 4,
            "outer_product_mean_dim_hidden": 4,
            "msa_pwa_heads": 1,
            "msa_pwa_dim_head": 4,
        },
        pairformer_stack={
            "depth": 1,
            "pair_bias_attn_dim_head": 2,
            "pair_bias_attn_heads": 2,
            "dropout_row_prob": 0.0,
        },
        diffusion_module_kwargs={
            "atom_encoder_depth": 1,
            "atom_encoder_heads": 1,
            "token_transformer_depth": 1,
            "token_transformer_heads": 1,
            "atom_decoder_depth": 1,
            "atom_decoder_heads": 1,
        },
        verbose=False,
    )


def tiny_forward(
    device_name: str,
    num_sample_steps: int,
    seed: int,
    with_confidence: bool = False,
    with_distogram: bool = False,
) -> int:
    import torch

    if not 2 <= num_sample_steps <= 4:
        raise ValueError(
            "--num-sample-steps must be between 2 and 4 for this safe probe; "
            "a one-step EDM schedule is degenerate"
        )
    with_confidence = with_confidence or with_distogram

    device = resolve_device(device_name)
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)

    model = build_tiny_model().to(device).eval()
    batch, tokens, atoms = 1, 2, 4
    lengths = torch.tensor([[2, 2]], dtype=torch.long, device=device)
    # Representative atoms are local positions in the flattened padded atom axis.
    molecule_atom_indices = torch.tensor([[0, 2]], dtype=torch.long, device=device)
    distogram_atom_indices = torch.tensor([[1, 3]], dtype=torch.long, device=device)
    atom_inputs = torch.randn(batch, atoms, 3, device=device)
    atompair_inputs = torch.randn(batch, atoms, atoms, 5, device=device)
    additional_molecule_feats = torch.zeros(batch, tokens, 5, dtype=torch.long, device=device)
    is_molecule_types = torch.zeros(batch, tokens, 5, dtype=torch.bool, device=device)
    is_molecule_types[..., 0] = True
    molecule_ids = torch.tensor([[0, 1]], dtype=torch.long, device=device)
    additional_token_feats = torch.zeros(batch, tokens, 33, device=device)

    with torch.no_grad():
        coords = model(
            atom_inputs=atom_inputs,
            atompair_inputs=atompair_inputs,
            additional_molecule_feats=additional_molecule_feats,
            is_molecule_types=is_molecule_types,
            molecule_atom_lens=lengths,
            molecule_ids=molecule_ids,
            additional_token_feats=additional_token_feats,
            molecule_atom_indices=molecule_atom_indices,
            distogram_atom_indices=distogram_atom_indices,
            num_recycling_steps=1,
            num_sample_steps=num_sample_steps,
            return_loss=False,
            return_confidence_head_logits=with_confidence,
            return_distogram_head_logits=with_distogram,
        )

    logits = None
    if with_confidence:
        coords, logits = coords
    if not isinstance(coords, torch.Tensor) or tuple(coords.shape) != (batch, atoms, 3):
        raise RuntimeError(f"unexpected tiny sample shape: {getattr(coords, 'shape', None)}")
    if not torch.isfinite(coords).all():
        raise RuntimeError("tiny sample contains non-finite coordinates")
    if with_confidence:
        if not all(torch.isfinite(value).all() for value in logits if value is not None):
            raise RuntimeError("tiny confidence output contains non-finite logits")
        if tuple(logits.plddt.shape[-1:]) != (atoms,) or tuple(logits.resolved.shape[-1:]) != (atoms,):
            raise RuntimeError("tiny confidence atom-logit shapes do not match the atom axis")
        print(
            f"confidence logits: pae={getattr(logits.pae, 'shape', None)} "
            f"pde={tuple(logits.pde.shape)} plddt={tuple(logits.plddt.shape)} "
            f"resolved={tuple(logits.resolved.shape)}"
        )
        if with_distogram:
            if logits.distance is None or not torch.isfinite(logits.distance).all():
                raise RuntimeError("tiny distogram output is missing or non-finite")
            print(f"distogram logits: shape={tuple(logits.distance.shape)}")
    print(f"tiny forward: OK device={device} shape={tuple(coords.shape)} steps={num_sample_steps}")
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "signature":
            return signature_check()
        return tiny_forward(
            args.device,
            args.num_sample_steps,
            args.seed,
            args.with_confidence,
            args.with_distogram,
        )
    except Exception as exc:  # provide a useful, non-destructive operator error
        message = str(exc)
        lowered = message.lower()
        if "out of memory" in lowered or "cudaerrormemoryallocation" in lowered:
            guidance = (
                "CUDA ran out of memory; retry on CPU or reduce the bounded model/input "
                "before attempting a larger workload."
            )
        elif isinstance(exc, (ImportError, ModuleNotFoundError)):
            guidance = (
                "A required Python dependency is unavailable; install the package's "
                "approved dependencies before retrying. No installation is attempted."
            )
        else:
            guidance = (
                "No files were changed. Fix the reported import, device, shape, or "
                "optional-dependency issue before retrying."
            )
        print(f"smoke_model: {type(exc).__name__}: {message}", file=sys.stderr)
        print(guidance, file=sys.stderr)
        if args.debug:
            raise
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
