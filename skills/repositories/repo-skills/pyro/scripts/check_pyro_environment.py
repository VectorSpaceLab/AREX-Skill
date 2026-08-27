#!/usr/bin/env python3
"""Check a Pyro runtime environment without needing the source checkout.

The script verifies core imports, reports package/backend versions, probes common
optional integrations, and can run a tiny CPU SVI smoke test. It is safe by
default: no downloads, no credentials, no long training, and no file mutation.
"""

import argparse
import importlib.util
import json
import math
from importlib.metadata import PackageNotFoundError, version


OPTIONAL_MODULES = {
    "funsor": "Funsor-backed enumeration and pyro.contrib.funsor workflows",
    "graphviz": "pyro.render_model graph rendering",
    "horovod": "distributed Horovod optimizer integration",
    "lightning": "PyTorch Lightning training example integration",
    "torchvision": "vision examples such as VAEs/CVAE/deep-kernel GP",
    "pandas": "dataframe-backed examples such as baseball/mixed HMM/CVAE",
    "scanpy": "scANVI full-data workflows",
    "zuko": "pyro.contrib.zuko flow adapter workflows",
}


def package_version(name: str):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def optional_imports():
    return {name: importlib.util.find_spec(name) is not None for name in OPTIONAL_MODULES}


def run_svi_smoke(num_steps: int = 3):
    import torch

    import pyro
    import pyro.distributions as dist
    from pyro.infer import SVI, Trace_ELBO
    from pyro.optim import Adam

    pyro.set_rng_seed(0)
    data = torch.randn(16) + 1.5

    def model(obs):
        loc = pyro.sample("loc", dist.Normal(obs.new_tensor(0.0), obs.new_tensor(5.0)))
        with pyro.plate("data", obs.size(0), dim=-1):
            pyro.sample("obs", dist.Normal(loc, obs.new_tensor(1.0)), obs=obs)

    def guide(obs):
        q_loc = pyro.param("q_loc", lambda: obs.new_tensor(0.0))
        q_scale = pyro.param(
            "q_scale",
            lambda: obs.new_tensor(0.5),
            constraint=dist.constraints.positive,
        )
        pyro.sample("loc", dist.Normal(q_loc, q_scale))

    pyro.clear_param_store()
    svi = SVI(model, guide, Adam({"lr": 0.02}), Trace_ELBO())
    losses = [float(svi.step(data)) for _ in range(num_steps)]
    if not all(math.isfinite(x) for x in losses):
        raise AssertionError(f"non-finite SVI losses: {losses!r}")
    return {
        "losses": losses,
        "q_loc": float(pyro.param("q_loc").detach()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report Pyro package, backend, optional integration, and tiny smoke-test status."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a text report",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run a tiny CPU SVI smoke test after import checks",
    )
    parser.add_argument(
        "--num-steps",
        type=int,
        default=3,
        help="SVI smoke steps when --smoke is used (default: 3)",
    )
    args = parser.parse_args()
    if args.num_steps <= 0:
        raise SystemExit("--num-steps must be positive")

    import torch

    import pyro
    import pyro.distributions  # noqa: F401
    import pyro.infer  # noqa: F401
    import pyro.nn  # noqa: F401
    import pyro.optim  # noqa: F401
    import pyro.poutine  # noqa: F401

    report = {
        "packages": {
            "pyro-ppl": package_version("pyro-ppl"),
            "pyro-api": package_version("pyro-api"),
            "torch": package_version("torch") or getattr(torch, "__version__", None),
            "numpy": package_version("numpy"),
            "opt-einsum": package_version("opt-einsum") or package_version("opt_einsum"),
            "tqdm": package_version("tqdm"),
        },
        "imports": {
            "pyro": getattr(pyro, "__version__", None),
            "pyro.distributions": True,
            "pyro.infer": True,
            "pyro.poutine": True,
            "pyro.nn": True,
            "pyro.optim": True,
        },
        "torch_backend": {
            "torch_version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        },
        "optional_modules": optional_imports(),
        "optional_module_purpose": OPTIONAL_MODULES,
    }

    if torch.cuda.is_available():
        report["torch_backend"]["cuda_device_name_0"] = torch.cuda.get_device_name(0)
        report["torch_backend"]["cuda_device_capability_0"] = torch.cuda.get_device_capability(0)

    if args.smoke:
        report["svi_smoke"] = run_svi_smoke(args.num_steps)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Pyro environment report")
        for key, value in report["packages"].items():
            print(f"package {key}: {value}")
        print(f"import pyro: {report['imports']['pyro']}")
        backend = report["torch_backend"]
        print(
            "torch backend: "
            f"version={backend['torch_version']} cuda_runtime={backend['cuda_runtime']} "
            f"cuda_available={backend['cuda_available']} cuda_device_count={backend['cuda_device_count']}"
        )
        print("optional modules:")
        for name, ok in sorted(report["optional_modules"].items()):
            status = "available" if ok else "missing"
            print(f"  {name}: {status} - {OPTIONAL_MODULES[name]}")
        if "svi_smoke" in report:
            smoke = report["svi_smoke"]
            print(f"svi_smoke losses={smoke['losses']} q_loc={smoke['q_loc']:.6g}")


if __name__ == "__main__":
    main()
