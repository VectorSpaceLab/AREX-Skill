#!/usr/bin/env python3
"""Safe PARL core backend alias checker.

This script imports PARL with an optional PARL_BACKEND value, prints the public
version and Model/Algorithm/Agent aliases, and can run a deterministic tiny
Torch weight-sync smoke when the Torch backend is selected.
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
import tempfile
from typing import Optional


BACKENDS = ("torch", "paddle", "fluid")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check PARL core backend aliases and optionally run a tiny Torch "
            "Model weight synchronization smoke."
        )
    )
    parser.add_argument(
        "--backend",
        choices=BACKENDS,
        help="Set PARL_BACKEND before importing PARL.",
    )
    parser.add_argument(
        "--torch-smoke",
        choices=("auto", "always", "never"),
        default="auto",
        help=(
            "Run a tiny Torch Model get/set/sync and Agent save/restore smoke: "
            "auto runs only when the selected backend is Torch."
        ),
    )
    return parser.parse_args()


def fail(message: str, exit_code: int = 2) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def import_parl(requested_backend: Optional[str]):
    if requested_backend:
        os.environ["PARL_BACKEND"] = requested_backend
    try:
        import parl  # pylint: disable=import-outside-toplevel
    except AssertionError as exc:
        if requested_backend == "torch":
            fail(
                "PARL_BACKEND=torch was requested, but Torch is not available "
                f"or PARL rejected the backend: {exc}"
            )
        fail(f"PARL rejected the requested backend: {exc}")
    except ModuleNotFoundError as exc:
        fail(
            "PARL could not import a backend dependency. Install the requested "
            f"backend package or choose another PARL_BACKEND. Original error: {exc}"
        )
    except ImportError as exc:
        fail(
            "PARL import failed while loading a backend dependency. Check that "
            f"the selected backend is installed and compatible. Original error: {exc}"
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        fail(f"unexpected error while importing PARL: {type(exc).__name__}: {exc}")
    return parl


def alias_name(parl, attr: str) -> Optional[str]:
    obj = getattr(parl, attr, None)
    if obj is None:
        return None
    module = getattr(obj, "__module__", "<unknown>")
    name = getattr(obj, "__name__", repr(obj))
    return f"{module}.{name}"


def infer_backend(model_alias: Optional[str]) -> str:
    if not model_alias:
        return "none"
    for backend in BACKENDS:
        if f".core.{backend}." in model_alias:
            return backend
    return "unknown"


def check_aliases(parl) -> str:
    print(f"parl_version: {getattr(parl, '__version__', '<unknown>')}")
    print(f"PARL_BACKEND_env: {os.environ.get('PARL_BACKEND', '<unset>')}")

    aliases = {name: alias_name(parl, name) for name in ("Model", "Algorithm", "Agent")}
    for name, value in aliases.items():
        print(f"alias_{name}: {value or '<missing>'}")

    missing = [name for name, value in aliases.items() if value is None]
    if missing:
        fail(
            "PARL imported but did not expose core aliases "
            f"{missing}. Install torch, paddle, or legacy fluid support, then set "
            "PARL_BACKEND before import."
        )

    detected = infer_backend(aliases["Model"])
    print(f"detected_backend: {detected}")
    if detected not in BACKENDS:
        fail(f"could not infer a supported backend from Model alias {aliases['Model']!r}")
    return detected


def print_framework_flags() -> None:
    try:
        from parl.utils import utils as parl_utils  # pylint: disable=import-outside-toplevel
    except Exception as exc:  # pragma: no cover - diagnostic only
        print(f"framework_flags: unavailable ({type(exc).__name__}: {exc})")
        return
    print(
        "framework_flags: "
        f"torch={bool(getattr(parl_utils, '_HAS_TORCH', False))} "
        f"paddle={bool(getattr(parl_utils, '_HAS_PADDLE', False))} "
        f"fluid={bool(getattr(parl_utils, '_HAS_FLUID', False))}"
    )


def run_torch_smoke(parl) -> None:
    try:
        import torch  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        fail(f"Torch smoke requested but torch is not importable: {exc}")

    torch.manual_seed(0)
    torch.set_num_threads(1)

    class TinyModel(parl.Model):
        def __init__(self):
            super().__init__()
            self.fc = torch.nn.Linear(2, 1)

        def forward(self, x):
            return self.fc(x)

        def value(self, x):
            return self.forward(x)

    class TinyAlgorithm(parl.Algorithm):
        def __init__(self, model):
            super().__init__(model)

        def predict(self, obs):
            return self.model.value(obs)

        def learn(self, *args, **kwargs):
            raise NotImplementedError("tiny smoke does not train")

    class TinyAgent(parl.Agent):
        def __init__(self, algorithm):
            super().__init__(algorithm)

        def predict(self, obs):
            return self.alg.predict(obs)

        def sample(self, obs):
            return self.predict(obs)

        def learn(self, *args, **kwargs):
            raise NotImplementedError("tiny smoke does not train")

    try:
        source = TinyModel()
        target = copy.deepcopy(source)
        with torch.no_grad():
            source.fc.weight.fill_(1.25)
            source.fc.bias.fill_(-0.5)
            target.fc.weight.fill_(-3.0)
            target.fc.bias.fill_(2.0)

        probe = torch.tensor([[2.0, -1.0]], dtype=torch.float32)
        source.sync_weights_to(target)
        if not torch.allclose(source(probe), target(probe)):
            fail("sync_weights_to completed but source and target outputs differ")

        weights = source.get_weights()
        target.set_weights(weights)
        if sorted(weights.keys()) != ["fc.bias", "fc.weight"]:
            fail(f"unexpected TinyModel weight keys: {sorted(weights.keys())}")

        agent = TinyAgent(TinyAlgorithm(target))
        expected = agent.predict(probe).detach().clone()
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = os.path.join(tmpdir, "tiny_model.pt")
            agent.save(checkpoint)
            with torch.no_grad():
                target.fc.bias.add_(3.0)
            agent.restore(checkpoint, map_location=torch.device("cpu"))
        restored = agent.predict(probe).detach()
        if not torch.allclose(expected, restored):
            fail("Agent restore completed but restored prediction differs")
    except RuntimeError as exc:
        if "Numpy" in str(exc) or "numpy" in str(exc):
            fail(
                "Torch smoke failed while converting weights through NumPy. "
                "Use a Torch and NumPy combination that supports tensor-to-NumPy conversion. "
                f"Original error: {exc}"
            )
        fail(f"Torch smoke failed: {exc}")
    except AssertionError as exc:
        fail(f"Torch smoke assertion failed: {exc}")

    print("torch_smoke: ok keys=fc.bias,fc.weight save_restore=ok")


def main() -> int:
    args = parse_args()
    parl = import_parl(args.backend)
    detected_backend = check_aliases(parl)
    print_framework_flags()

    if args.torch_smoke == "always" and detected_backend != "torch":
        fail(
            "--torch-smoke always requires the selected PARL backend to be torch. "
            "Run with --backend torch or set PARL_BACKEND=torch before import."
        )
    if args.torch_smoke == "always" or (
        args.torch_smoke == "auto" and detected_backend == "torch"
    ):
        run_torch_smoke(parl)
    else:
        print("torch_smoke: skipped")

    print("status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
