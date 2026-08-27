#!/usr/bin/env python3
"""Self-contained tiny Pyro NUTS smoke test on the eight-schools model.

The script embeds the canonical eight-schools data and runs a deliberately small
non-centered hierarchical model. It is intended to verify that Pyro's MCMC and
Predictive APIs execute in the active environment; the default sample counts are
not suitable for scientific posterior conclusions.
"""

import argparse
import math
from typing import Dict


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def tensor_shapes(values: Dict[str, "object"]) -> Dict[str, tuple]:
    return {name: tuple(value.shape) for name, value in sorted(values.items())}


def run(num_samples: int, warmup_steps: int, seed: int, disable_progbar: bool) -> None:
    import torch

    import pyro
    import pyro.distributions as dist
    from pyro.infer import MCMC, NUTS, Predictive

    y = torch.tensor([28.0, 8.0, -3.0, 7.0, -1.0, 1.0, 18.0, 12.0])
    sigma = torch.tensor([15.0, 10.0, 16.0, 11.0, 9.0, 11.0, 10.0, 18.0])

    def model(obs=None, obs_sigma=sigma):
        num_schools = obs_sigma.numel()
        eta = pyro.sample(
            "eta",
            dist.Normal(obs_sigma.new_zeros(num_schools), 1.0).to_event(1),
        )
        mu = pyro.sample("mu", dist.Normal(obs_sigma.new_tensor(0.0), 10.0))
        tau = pyro.sample("tau", dist.HalfCauchy(obs_sigma.new_tensor(25.0)))
        theta = pyro.deterministic("theta", mu + tau * eta, event_dim=1)
        with pyro.plate("school", num_schools, dim=-1):
            pyro.sample("obs", dist.Normal(theta, obs_sigma), obs=obs)

    pyro.set_rng_seed(seed)
    pyro.clear_param_store()
    pyro.enable_validation(True)

    kernel = NUTS(model, target_accept_prob=0.8, max_tree_depth=4)
    mcmc = MCMC(
        kernel,
        num_samples=num_samples,
        warmup_steps=warmup_steps,
        disable_progbar=disable_progbar,
        disable_validation=False,
    )
    mcmc.run(y, sigma)
    samples = mcmc.get_samples()

    if not samples:
        raise AssertionError("MCMC returned no latent samples")
    for name, value in samples.items():
        if not torch.isfinite(value).all():
            raise AssertionError(f"non-finite posterior sample at site {name!r}")

    predictive = Predictive(
        model,
        posterior_samples=samples,
        return_sites=["theta", "obs"],
        parallel=False,
    )
    predictive_samples = predictive(None, sigma)
    for name, value in predictive_samples.items():
        if not torch.isfinite(value).all():
            raise AssertionError(f"non-finite predictive sample at site {name!r}")

    diagnostic_error = None
    try:
        diagnostics = mcmc.diagnostics()
    except AssertionError as exc:
        # Some diagnostics, especially split R-hat, require at least four
        # retained samples per chain. Keep very tiny smoke runs usable.
        diagnostics = {}
        diagnostic_error = f"diagnostics_unavailable_for_tiny_run: {exc}"
    divergence_count = 0
    if "divergences" in diagnostics:
        divergence_count = sum(len(v) for v in diagnostics["divergences"].values())

    print(f"pyro_version={pyro.__version__}")
    print(f"seed={seed}")
    print(f"num_samples={num_samples}")
    print(f"warmup_steps={warmup_steps}")
    print(f"posterior_sample_shapes={tensor_shapes(samples)}")
    print(f"predictive_sample_shapes={tensor_shapes(predictive_samples)}")
    print(f"diagnostic_keys={sorted(diagnostics)}")
    if diagnostic_error is not None:
        print(diagnostic_error)
    print(f"divergence_count={divergence_count}")

    # A tiny run is allowed to have poor convergence, but the model should at
    # least produce finite tensors and the requested number of retained samples.
    for value in samples.values():
        if value.shape[0] != num_samples:
            raise AssertionError("unexpected retained posterior sample count")
    if not math.isfinite(float(samples["mu"].mean())):
        raise AssertionError("posterior mean smoke statistic is not finite")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a tiny self-contained Pyro eight-schools NUTS smoke test."
    )
    parser.add_argument(
        "--num-samples",
        type=positive_int,
        default=8,
        help="number of retained MCMC samples (default: 8)",
    )
    parser.add_argument(
        "--warmup-steps",
        type=positive_int,
        default=8,
        help="number of warmup/adaptation steps (default: 8)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="random seed (default: 0)",
    )
    parser.add_argument(
        "--disable-progbar",
        action="store_true",
        help="disable Pyro's MCMC progress bar for non-interactive logs",
    )
    args = parser.parse_args()
    run(args.num_samples, args.warmup_steps, args.seed, args.disable_progbar)


if __name__ == "__main__":
    main()
