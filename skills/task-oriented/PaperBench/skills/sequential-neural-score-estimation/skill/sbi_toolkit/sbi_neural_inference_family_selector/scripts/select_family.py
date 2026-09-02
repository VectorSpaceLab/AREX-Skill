#!/usr/bin/env python3
import argparse
import json


def select_family(target, direct_sampling=False, mcmc_ok=False, density_eval_required=False):
    normalized = target.lower().strip()
    if normalized in {"posterior", "p(theta|x)", "conditional_posterior"}:
        return {
            "family": "SNPE",
            "objective": "learn p(theta | x) directly from simulated pairs",
            "posterior_requires_mcmc": False,
            "limitations": [] if not density_eval_required else ["density evaluation depends on posterior estimator support"],
        }
    if normalized in {"likelihood", "p(x|theta)"}:
        if direct_sampling and not mcmc_ok:
            raise ValueError("SNLE posterior construction generally requires MCMC or another sampler")
        return {
            "family": "SNLE",
            "objective": "learn p(x | theta), then combine with prior for posterior sampling",
            "posterior_requires_mcmc": True,
            "limitations": ["posterior sampling requires a sampler such as MCMC"],
        }
    if normalized in {"ratio", "likelihood_ratio", "density_ratio"}:
        if density_eval_required:
            raise ValueError("SNRE estimates density ratios, not direct likelihood values")
        return {
            "family": "SNRE",
            "objective": "learn likelihood-to-evidence or pairwise density ratios with a classifier",
            "posterior_requires_mcmc": True,
            "limitations": ["ratio estimates require posterior sampling machinery"],
        }
    raise ValueError(f"unknown target: {target}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--direct-sampling", action="store_true")
    parser.add_argument("--mcmc-ok", action="store_true")
    parser.add_argument("--density-eval-required", action="store_true")
    args = parser.parse_args()
    result = select_family(args.target, args.direct_sampling, args.mcmc_ok, args.density_eval_required)
    print(json.dumps({"ok": True, **result}, indent=2))


if __name__ == "__main__":
    main()
