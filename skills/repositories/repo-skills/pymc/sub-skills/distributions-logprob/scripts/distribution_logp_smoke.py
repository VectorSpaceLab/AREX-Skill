#!/usr/bin/env python3
"""Tiny PyMC distribution/logp smoke."""
from __future__ import annotations

import argparse
import json
import warnings
from typing import Any

import numpy as np


def shape(value: Any) -> tuple[int, ...]:
    return tuple(np.asarray(value).shape)


def run(seed: int = 123, draws: int = 2) -> dict[str, Any]:
    import pymc as pm
    import pytensor.tensor as pt

    warnings.filterwarnings("ignore", message=r"Numba will use object mode to run CustomDist.*", category=UserWarning)
    rng = np.random.default_rng(seed)
    observed = rng.normal(size=3)

    def logp(value, mu):
        return pm.logp(pm.Normal.dist(mu=mu, sigma=1.0), value)

    def random(mu, rng=None, size=None):
        return rng.normal(loc=mu, scale=1.0, size=size)

    def logcdf(value, mu):
        return pm.logcdf(pm.Normal.dist(mu=mu, sigma=1.0), value)

    def support_point(rv, size, mu):
        return pt.full(size, mu, dtype=rv.dtype)

    custom = pm.CustomDist.dist(0.0, logp=logp, random=random, logcdf=logcdf, support_point=support_point, signature="()->()", shape=(3,))
    custom_draw = pm.draw(custom, draws=draws, random_seed=seed)
    custom_logp = pm.logp(custom, observed).eval()
    custom_logcdf = pm.logcdf(custom, observed).eval()

    weights = np.array([0.25, 0.75])
    component = pm.Normal.dist(mu=np.array([-1.0, 1.0]), sigma=np.array([0.5, 0.5]), shape=(4, 2))
    mixture = pm.Mixture.dist(w=weights, comp_dists=component)
    mixture_draw = pm.draw(mixture, draws=draws, random_seed=seed + 1)
    mixture_logp = pm.logp(mixture, np.zeros(4)).eval()

    mvn = pm.MvNormal.dist(mu=np.zeros(2), cov=np.eye(2), size=(3,))
    mvn_draw = pm.draw(mvn, draws=1, random_seed=seed + 2)
    mvn_logp = pm.logp(mvn, np.zeros((3, 2))).eval()

    with pm.Model() as model:
        mu = pm.Normal("mu", 0, 1)
        pm.CustomDist("obs", mu, logp=logp, random=random, logcdf=logcdf, support_point=support_point, signature="()->()", observed=observed)
        keys = sorted(model.point_logps())

    checks = {
        "custom_draw_shape": shape(custom_draw),
        "custom_logp_shape": shape(custom_logp),
        "custom_logcdf_shape": shape(custom_logcdf),
        "mixture_draw_shape": shape(mixture_draw),
        "mixture_logp_shape": shape(mixture_logp),
        "mvn_draw_shape": shape(mvn_draw),
        "mvn_logp_shape": shape(mvn_logp),
        "point_logps_keys": keys,
    }
    assert checks["custom_draw_shape"] == (draws, 3)
    assert checks["custom_logp_shape"] == (3,)
    assert checks["mixture_draw_shape"] == (draws, 4)
    assert checks["mvn_logp_shape"] == (3,)
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate tiny PyMC CustomDist, Mixture .dist(), pm.logp/logcdf, and shape patterns.")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--draws", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run(args.seed, args.draws)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else "PyMC distribution/logp smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
