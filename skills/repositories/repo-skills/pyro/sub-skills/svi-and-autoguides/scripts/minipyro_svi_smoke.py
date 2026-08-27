#!/usr/bin/env python3
"""Tiny deterministic Pyro SVI smoke test.

This is a self-contained, short CPU check inspired by the MiniPyro SVI example:
a one-dimensional Normal latent location is fit to synthetic observations.  It
asserts finite losses and parameters, then prints the learned variational loc.
"""

import argparse
import math


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite float")
    return parsed


def run(num_steps: int, learning_rate: float, seed: int) -> float:
    import torch
    from torch.distributions import constraints

    import pyro
    import pyro.distributions as dist
    from pyro.infer import SVI, Trace_ELBO
    from pyro.optim import Adam

    def build_data() -> torch.Tensor:
        pyro.set_rng_seed(seed)
        base = torch.linspace(-1.0, 1.0, 32)
        noise = 0.05 * torch.randn(base.shape)
        return 2.5 + base + noise

    def model(data: torch.Tensor) -> None:
        loc = pyro.sample(
            "loc", dist.Normal(data.new_tensor(0.0), data.new_tensor(5.0))
        )
        with pyro.plate("data", data.size(0), dim=-1):
            pyro.sample("obs", dist.Normal(loc, data.new_tensor(1.0)), obs=data)

    def guide(data: torch.Tensor) -> None:
        guide_loc = pyro.param("guide_loc", lambda: data.new_tensor(0.0))
        guide_scale = pyro.param(
            "guide_scale",
            lambda: data.new_tensor(0.5),
            constraint=constraints.positive,
        )
        pyro.sample("loc", dist.Normal(guide_loc, guide_scale))

    data = build_data()
    pyro.clear_param_store()
    svi = SVI(model, guide, Adam({"lr": learning_rate}), Trace_ELBO())

    losses = []
    for step in range(num_steps):
        loss = svi.step(data)
        if not math.isfinite(loss):
            raise AssertionError(f"non-finite loss at step {step}: {loss!r}")
        losses.append(loss)

    learned_loc = pyro.param("guide_loc").detach()
    learned_scale = pyro.param("guide_scale").detach()
    if not torch.isfinite(learned_loc).all() or not torch.isfinite(learned_scale).all():
        raise AssertionError("learned variational parameters are not finite")
    if learned_loc.abs().item() <= 0.0:
        raise AssertionError("guide_loc did not move from its initialization")

    print(f"pyro_version={pyro.__version__}")
    print(f"num_steps={num_steps}")
    print(f"initial_loss={losses[0]:.6g}")
    print(f"final_loss={losses[-1]:.6g}")
    print(f"learned_loc={learned_loc.item():.6g}")
    print(f"learned_scale={learned_scale.item():.6g}")
    return learned_loc.item()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic Pyro SVI smoke test."
    )
    parser.add_argument(
        "--num-steps",
        type=positive_int,
        default=40,
        help="number of SVI steps to run (default: 40)",
    )
    parser.add_argument(
        "--learning-rate",
        type=positive_float,
        default=0.05,
        help="Adam learning rate (default: 0.05)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="random seed for deterministic synthetic data (default: 0)",
    )
    args = parser.parse_args()
    run(args.num_steps, args.learning_rate, args.seed)


if __name__ == "__main__":
    main()
