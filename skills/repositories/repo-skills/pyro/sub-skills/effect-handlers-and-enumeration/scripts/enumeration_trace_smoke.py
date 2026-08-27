#!/usr/bin/env python3
"""Tiny Pyro enumeration + poutine trace smoke test.

This self-contained CPU script builds a two-component Gaussian mixture with a
model-enumerated Categorical latent site. It computes a finite TraceEnum_ELBO
loss, traces the enumerated model to print site shapes, then uses infer_discrete
to decode posterior latent assignments. It does not require the Pyro source
checkout or optional extras.
"""

import argparse
import math
from typing import Iterable


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


def make_data(num_obs: int, seed: int):
    import torch

    generator = torch.Generator().manual_seed(seed)
    centers = torch.tensor([-1.0, 1.0])
    assignments = torch.arange(num_obs) % 2
    noise = 0.08 * torch.randn(num_obs, generator=generator)
    return centers[assignments] + noise


def summarize_trace(trace) -> Iterable[str]:
    for name, site in trace.nodes.items():
        if site["type"] == "sample":
            value_shape = tuple(site["value"].shape)
            log_prob_shape = (
                tuple(site["log_prob"].shape) if "log_prob" in site else None
            )
            enum_dim = site["infer"].get("_enumerate_dim")
            observed = site["is_observed"]
            plates = [
                (frame.name, frame.dim, frame.size) for frame in site["cond_indep_stack"]
            ]
            yield (
                f"site={name} observed={observed} value_shape={value_shape} "
                f"log_prob_shape={log_prob_shape} enum_dim={enum_dim} plates={plates}"
            )


def run(num_obs: int, obs_scale: float, seed: int, temperature: int) -> float:
    import torch

    import pyro
    import pyro.distributions as dist
    import pyro.poutine as poutine
    from pyro.infer import TraceEnum_ELBO, config_enumerate, infer_discrete
    from pyro.ops.indexing import Vindex

    if temperature not in (0, 1):
        raise AssertionError("temperature must be 0 for MAP or 1 for posterior sampling")

    pyro.enable_validation(True)
    pyro.set_rng_seed(seed)
    data = make_data(num_obs, seed)
    max_plate_nesting = 1
    first_available_dim = -1 - max_plate_nesting

    @config_enumerate
    def model(observations):
        weights = torch.tensor([0.5, 0.5])
        locs = torch.tensor([-1.0, 1.0])
        scale = torch.tensor(obs_scale)
        with pyro.plate("data", observations.size(0), dim=-1):
            z = pyro.sample(
                "z",
                dist.Categorical(weights),
                infer={"enumerate": "parallel"},
            )
            pyro.sample("x", dist.Normal(Vindex(locs)[z], scale), obs=observations)
        return z

    def guide(observations):
        # Empty guide: z is model-enumerated and marginalized by TraceEnum_ELBO.
        return None

    pyro.clear_param_store()
    elbo = TraceEnum_ELBO(max_plate_nesting=max_plate_nesting)
    loss = elbo.loss(model, guide, data)
    if not math.isfinite(loss):
        raise AssertionError(f"TraceEnum_ELBO produced non-finite loss: {loss!r}")

    enum_trace = poutine.trace(
        poutine.enum(model, first_available_dim=first_available_dim)
    ).get_trace(data)
    enum_trace.compute_log_prob()

    decoded_model = infer_discrete(
        model,
        first_available_dim=first_available_dim,
        temperature=temperature,
    )
    decoded_trace = poutine.trace(decoded_model).get_trace(data)
    decoded_values = decoded_trace.nodes["z"]["value"].detach().cpu().tolist()

    print(f"pyro_version={pyro.__version__}")
    print(f"num_obs={num_obs}")
    print(f"temperature={temperature}")
    print(f"finite_loss={loss:.6g}")
    print("enumerated_trace_shapes:")
    print(enum_trace.format_shapes())
    print("enumerated_trace_sites:")
    for line in summarize_trace(enum_trace):
        print("  " + line)
    print(f"decoded_z={decoded_values}")
    return float(loss)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a tiny Pyro poutine trace + discrete enumeration smoke test."
    )
    parser.add_argument(
        "--num-obs",
        type=positive_int,
        default=8,
        help="number of synthetic observations (default: 8)",
    )
    parser.add_argument(
        "--obs-scale",
        type=positive_float,
        default=0.35,
        help="known Normal observation scale (default: 0.35)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="random seed for deterministic synthetic data (default: 0)",
    )
    parser.add_argument(
        "--temperature",
        type=int,
        choices=[0, 1],
        default=0,
        help="infer_discrete mode: 0=MAP, 1=posterior sample (default: 0)",
    )
    args = parser.parse_args()
    run(args.num_obs, args.obs_scale, args.seed, args.temperature)


if __name__ == "__main__":
    main()
