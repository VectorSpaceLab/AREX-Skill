#!/usr/bin/env python3
"""Print key public NumPyro API signatures as JSON.

Use this when a future agent needs to confirm the installed package's current
surface before writing code. It performs read-only imports and signature
inspection only.
"""

from __future__ import annotations

import argparse
import inspect
import json
from typing import Any


def maybe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<signature unavailable: {exc.__class__.__name__}>"


def run() -> dict[str, Any]:
    import numpyro
    from numpyro import handlers
    import numpyro.distributions as dist
    from numpyro.infer import MCMC, NUTS, HMC, SVI, Trace_ELBO, TraceEnum_ELBO, Predictive, log_likelihood
    from numpyro.infer import autoguide
    from numpyro.infer import reparam

    objects = {
        "numpyro.sample": numpyro.sample,
        "numpyro.param": numpyro.param,
        "numpyro.plate": numpyro.plate,
        "numpyro.deterministic": numpyro.deterministic,
        "handlers.seed": handlers.seed,
        "handlers.trace": handlers.trace,
        "handlers.condition": handlers.condition,
        "handlers.reparam": handlers.reparam,
        "dist.Normal": dist.Normal,
        "dist.Beta": dist.Beta,
        "dist.Bernoulli": dist.Bernoulli,
        "dist.MultivariateNormal": dist.MultivariateNormal,
        "dist.TransformedDistribution": dist.TransformedDistribution,
        "MCMC": MCMC,
        "NUTS": NUTS,
        "HMC": HMC,
        "SVI": SVI,
        "Trace_ELBO": Trace_ELBO,
        "TraceEnum_ELBO": TraceEnum_ELBO,
        "Predictive": Predictive,
        "log_likelihood": log_likelihood,
        "AutoNormal": autoguide.AutoNormal,
        "AutoDelta": autoguide.AutoDelta,
        "AutoGuideList": autoguide.AutoGuideList,
        "LocScaleReparam": reparam.LocScaleReparam,
        "TransformReparam": reparam.TransformReparam,
        "NeuTraReparam": reparam.NeuTraReparam,
    }
    return {
        "numpyro_version": getattr(numpyro, "__version__", None),
        "signatures": {name: maybe_signature(obj) for name, obj in objects.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Print key NumPyro API signatures as JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()
    print(json.dumps(run(), indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
