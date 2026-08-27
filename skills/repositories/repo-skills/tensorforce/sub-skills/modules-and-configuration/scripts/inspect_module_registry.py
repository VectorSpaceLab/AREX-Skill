#!/usr/bin/env python3
"""Print Tensorforce module registry names from an installed package."""

import argparse
import json
import sys


def names(module_name, attr):
    module = __import__(module_name, fromlist=[attr])
    value = getattr(module, attr, {})
    if isinstance(value, dict):
        return sorted(str(k) for k in value.keys())
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect Tensorforce module registries.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)
    try:
        import tensorforce
        data = {
            "version": getattr(tensorforce, "__version__", "unknown"),
            "agents": names("tensorforce.agents", "agents"),
            "environments": names("tensorforce.environments", "environments"),
            "layers": names("tensorforce.core.layers", "layer_modules"),
            "networks": names("tensorforce.core.networks", "network_modules"),
            "memories": names("tensorforce.core.memories", "memory_modules"),
            "objectives": names("tensorforce.core.objectives", "objective_modules"),
            "optimizers": names("tensorforce.core.optimizers", "optimizer_modules"),
            "parameters": names("tensorforce.core.parameters", "parameter_modules"),
            "policies": names("tensorforce.core.policies", "policy_modules"),
        }
    except Exception as exc:
        print("Failed to inspect Tensorforce registries: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        for family, values in data.items():
            if isinstance(values, list):
                print("{}: {}".format(family, ", ".join(values)))
            else:
                print("{}: {}".format(family, values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
