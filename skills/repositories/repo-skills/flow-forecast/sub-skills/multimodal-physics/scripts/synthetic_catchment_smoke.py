#!/usr/bin/env python3
"""Run a tiny synthetic smoke test for Flow Forecast multimodal hydrology.

The script builds a temporary catchment `.npz` dataset, pretrains the catchment
encoder for one short epoch, extracts embeddings, runs the GR4 hybrid model, and
performs a direct NeuralODE integration on the same forcing/times.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import numpy as np
import torch

from flood_forecast.meta_models.merging_model import GatedFusion, MergingModel
from flood_forecast.multi_models.catchment_embedding import CatchmentEncoder
from flood_forecast.multi_models.contrastive_pretrain import extract_embeddings, pretrain_catchment_encoder
from flood_forecast.ode.neural_ode import NeuralODE
from flood_forecast.ode.physics.hydrology import GR4Dynamics, HybridGR4Model
from flood_forecast.preprocessing.catchment_loader import CatchmentEmbeddingDataset


@contextmanager
def _temp_cwd(path: Path) -> Iterator[None]:
    """Temporarily change the current working directory.

    :param path: Directory to enter.
    :type path: pathlib.Path
    :return: Context manager with no yielded value.
    :rtype: typing.Iterator[None]
    """
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _build_site_record(site_id: str, destination: Path, *, rng: np.random.Generator) -> None:
    """Create one synthetic catchment record.

    :param site_id: Site identifier.
    :type site_id: str
    :param destination: Destination directory.
    :type destination: pathlib.Path
    :param rng: Random number generator.
    :type rng: numpy.random.Generator
    :return: None
    :rtype: None
    """
    destination.mkdir(parents=True, exist_ok=True)
    image = (rng.random((3, 16, 16)).astype(np.float32) * 3000.0)
    static = rng.normal(size=(4,)).astype(np.float32)
    history = rng.normal(loc=25.0, scale=5.0, size=(40,)).astype(np.float32)
    history[rng.choice(len(history), size=8, replace=False)] = np.nan
    np.savez(destination / f"{site_id}.npz", image=image, static=static, history=history)


def _build_fixture_dataset(destination: Path, site_count: int = 3) -> Path:
    """Build a small directory of catchment records.

    :param destination: Destination directory.
    :type destination: pathlib.Path
    :param site_count: Number of sites to create.
    :type site_count: int
    :return: The dataset directory.
    :rtype: pathlib.Path
    """
    rng = np.random.default_rng(0)
    for index in range(site_count):
        _build_site_record(f"site_{index}", destination, rng=rng)
    return destination


def _run_fusion_smoke(device: str) -> None:
    """Exercise the generic fusion helpers.

    :param device: Torch device string.
    :type device: str
    :return: None
    :rtype: None
    """
    temporal = torch.randn(2, 8, 32, device=device)
    context = torch.randn(2, 64, device=device)
    gate = GatedFusion(hidden_dim=32, context_dim=64).to(device)
    merged = gate(temporal, context)
    wrapper = MergingModel("Concat", {"cat_dim": 2, "repeat": True, "use_layer": False, "combined_d": 96, "out_shape": 96}).to(device)
    wrapped = wrapper(temporal, context)
    print("Fusion smoke shapes:", tuple(merged.shape), tuple(wrapped.shape))


def _run_hydrology_smoke(device: str, dataset: CatchmentEmbeddingDataset) -> None:
    """Run the hybrid GR4 and direct NeuralODE smoke.

    :param device: Torch device string.
    :type device: str
    :param dataset: The dataset used to generate context embeddings.
    :type dataset: CatchmentEmbeddingDataset
    :return: None
    :rtype: None
    """
    encoder = CatchmentEncoder(
        image_size=16,
        image_channels=3,
        static_features=dataset.static_features,
        history_features=2,
        history_len=12,
        patch_size=8,
        dim=32,
        embedding_dim=64,
        depth=2,
        heads=2,
        dim_head=16,
        dropout=0.0,
        fusion="concat",
    )
    losses = pretrain_catchment_encoder(encoder, dataset, epochs=1, batch_size=2, lr=1e-3, device=device)
    site_ids, embeddings = extract_embeddings(encoder, dataset, batch_size=2, device=device, n_history_samples=1)
    print("Pretraining loss:", losses[-1])
    print("Sites:", ", ".join(site_ids))
    print("Embedding shape:", tuple(embeddings.shape))

    hybrid = HybridGR4Model(
        n_met_features=3,
        seq_len=8,
        context_dim=64,
        dim=32,
        depth=1,
        heads=2,
        n_routing_reservoirs=3,
        solver_params={"method": "rk4"},
        encoder_type="transformer",
    ).to(device)
    met = torch.randn(2, 8, 3, device=device)
    context = embeddings[:2].to(device)
    result = hybrid(met, context)
    print("Hybrid keys:", ", ".join(sorted(result)))
    print("Flow shape:", tuple(result["flow"].shape))

    dynamics = GR4Dynamics(learnable=False).to(device)
    dynamics.set_parameters(result["parameters"])
    dynamics.set_forcing(result["forcing"], hybrid.times)
    node = NeuralODE(dynamics, method="rk4")
    initial_state = torch.zeros(2, dynamics.state_dim, device=device)
    initial_state[:, 0] = 0.6 * result["parameters"][:, 0]
    initial_state[:, 1] = 0.3 * result["parameters"][:, 2]
    states = node(initial_state, hybrid.times)
    streamflow = dynamics.streamflow(states)
    print("Direct NeuralODE states:", tuple(states.shape))
    print("Direct streamflow:", tuple(streamflow.shape))


def main(argv: list[str] | None = None) -> int:
    """Run the synthetic multimodal smoke test.

    :param argv: Optional argument vector.
    :type argv: list[str] | None
    :return: Process exit status.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description="Run a tiny synthetic catchment/hydrology smoke test.")
    parser.add_argument("--device", default="cpu", help="Torch device to use. Defaults to cpu.")
    parser.add_argument("--sites", type=int, default=3, help="Number of synthetic catchment records to create.")
    parser.add_argument("--skip-hydrology", action="store_true", help="Only run the dataset and fusion smoke.")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        dataset_dir = _build_fixture_dataset(temp_path / "catchments", site_count=args.sites)
        dataset = CatchmentEmbeddingDataset(str(dataset_dir), history_window_days=12, seed=0)
        with _temp_cwd(temp_path):
            sample = dataset[0]
            print("Sample keys:", ", ".join(sorted(sample)))
            print("Sample image shape:", tuple(sample["image"].shape))
            print("Sample history shape:", tuple(sample["history"].shape))
            _run_fusion_smoke(args.device)
            if not args.skip_hydrology:
                _run_hydrology_smoke(args.device, dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
