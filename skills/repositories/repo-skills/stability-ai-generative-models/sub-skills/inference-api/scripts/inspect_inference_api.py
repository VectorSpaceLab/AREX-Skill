#!/usr/bin/env python3
"""Inspect the installed sgm.inference API without loading checkpoints."""

from __future__ import annotations

import argparse
import dataclasses
import enum
import importlib
import inspect
import json
import sys
from typing import Any


EXPECTED = {
    "architectures": {
        "stable-diffusion-xl-v0-9-base",
        "stable-diffusion-xl-v0-9-refiner",
        "stable-diffusion-xl-v1-base",
        "stable-diffusion-xl-v1-refiner",
    },
    "samplers": {
        "EulerEDMSampler",
        "HeunEDMSampler",
        "EulerAncestralSampler",
        "DPMPP2SAncestralSampler",
        "DPMPP2MSampler",
        "LinearMultistepSampler",
    },
    "discretizations": {"LegacyDDPMDiscretization", "EDMDiscretization"},
    "guiders": {"VanillaCFG", "IdentityGuider"},
    "configs": {"sd_xl_base.yaml", "sd_xl_refiner.yaml"},
}


def sanitize_error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc).splitlines()[0] if str(exc) else ""}


def signature_of(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def enum_values(cls: Any) -> list[str]:
    if isinstance(cls, type) and issubclass(cls, enum.Enum):
        return [member.value for member in cls]
    return []


def dataclass_defaults(cls: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for field in dataclasses.fields(cls):
        value = field.default
        if isinstance(value, enum.Enum):
            value = value.value
        elif value is dataclasses.MISSING:
            value = None
        defaults[field.name] = value
    return defaults


def dataclass_dict(obj: Any) -> dict[str, Any]:
    data = dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else dict(obj)
    return {key: (value.value if isinstance(value, enum.Enum) else value) for key, value in data.items()}


def collect_info() -> tuple[dict[str, Any], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    info: dict[str, Any] = {"loads_checkpoints": False}

    try:
        sgm = importlib.import_module("sgm")
        info["sgm_version"] = getattr(sgm, "__version__", "unknown")
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append({"module": "sgm", **sanitize_error(exc)})
        return info, errors

    try:
        api = importlib.import_module("sgm.inference.api")
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append({"module": "sgm.inference.api", **sanitize_error(exc)})
        return info, errors

    try:
        helpers = importlib.import_module("sgm.inference.helpers")
    except Exception as exc:  # pragma: no cover - environment dependent
        helpers = None
        errors.append({"module": "sgm.inference.helpers", **sanitize_error(exc)})

    info["signatures"] = {
        "SamplingPipeline.__init__": signature_of(api.SamplingPipeline.__init__),
        "SamplingPipeline.text_to_image": signature_of(api.SamplingPipeline.text_to_image),
        "SamplingPipeline.image_to_image": signature_of(api.SamplingPipeline.image_to_image),
        "SamplingPipeline.refiner": signature_of(api.SamplingPipeline.refiner),
        "get_sampler_config": signature_of(api.get_sampler_config),
        "get_discretization_config": signature_of(api.get_discretization_config),
        "get_guider_config": signature_of(api.get_guider_config),
    }

    if helpers is not None:
        info["helper_signatures"] = {
            "get_input_image_tensor": signature_of(helpers.get_input_image_tensor),
            "Img2ImgDiscretizationWrapper.__init__": signature_of(helpers.Img2ImgDiscretizationWrapper.__init__),
            "do_sample": signature_of(helpers.do_sample),
            "do_img2img": signature_of(helpers.do_img2img),
            "get_batch": signature_of(helpers.get_batch),
        }

    info["enums"] = {
        "ModelArchitecture": enum_values(api.ModelArchitecture),
        "Sampler": enum_values(api.Sampler),
        "Discretization": enum_values(api.Discretization),
        "Guider": enum_values(api.Guider),
    }
    if hasattr(api, "Thresholder"):
        info["enums"]["Thresholder"] = enum_values(api.Thresholder)

    info["sampling_params_defaults"] = dataclass_defaults(api.SamplingParams)
    info["model_specs"] = {
        key.value if isinstance(key, enum.Enum) else str(key): dataclass_dict(value)
        for key, value in api.model_specs.items()
    }
    return info, errors


def assertion_failures(info: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    enums = info.get("enums", {})
    model_specs = info.get("model_specs", {})

    checks = {
        "architectures": set(enums.get("ModelArchitecture", [])),
        "samplers": set(enums.get("Sampler", [])),
        "discretizations": set(enums.get("Discretization", [])),
        "guiders": set(enums.get("Guider", [])),
        "configs": {spec.get("config") for spec in model_specs.values()},
    }
    for name, expected in EXPECTED.items():
        missing = sorted(expected - checks.get(name, set()))
        if missing:
            failures.append(f"missing {name}: {', '.join(missing)}")

    expected_defaults = {
        "width": 1024,
        "height": 1024,
        "steps": 50,
        "sampler": "DPMPP2MSampler",
        "discretization": "LegacyDDPMDiscretization",
        "guider": "VanillaCFG",
        "scale": 6.0,
        "img2img_strength": 1.0,
        "sigma_min": 0.0292,
        "sigma_max": 14.6146,
        "rho": 3.0,
        "order": 4,
    }
    defaults = info.get("sampling_params_defaults", {})
    for field, expected in expected_defaults.items():
        if defaults.get(field) != expected:
            failures.append(f"unexpected SamplingParams.{field}: {defaults.get(field)!r}")

    return failures


def print_text(info: dict[str, Any], errors: list[dict[str, str]], failures: list[str]) -> None:
    print(f"sgm version: {info.get('sgm_version', 'unavailable')}")
    print(f"loads checkpoints: {info.get('loads_checkpoints', False)}")

    if errors:
        print("import errors:")
        for error in errors:
            print(f"  - {error.get('module')}: {error.get('type')}: {error.get('message')}")

    if "signatures" in info:
        print("signatures:")
        for name, sig in info["signatures"].items():
            print(f"  - {name}{sig}")

    if "enums" in info:
        print("enums:")
        for name, values in info["enums"].items():
            print(f"  - {name}: {', '.join(values)}")

    if "model_specs" in info:
        print("model specs:")
        for architecture, spec in info["model_specs"].items():
            print(f"  - {architecture}: config={spec.get('config')} ckpt={spec.get('ckpt')}")

    if failures:
        print("assertion failures:")
        for failure in failures:
            print(f"  - {failure}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect installed sgm.inference.api facts without constructing SamplingPipeline or loading checkpoints."
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument(
        "--assert-expected",
        action="store_true",
        help="exit nonzero if expected SDXL API names/defaults are missing",
    )
    args = parser.parse_args(argv)

    info, errors = collect_info()
    failures = assertion_failures(info) if args.assert_expected and not errors else []
    exit_code = 1 if errors or failures else 0

    if args.json:
        print(json.dumps({"ok": exit_code == 0, "info": info, "errors": errors, "failures": failures}, indent=2, sort_keys=True))
    else:
        print_text(info, errors, failures)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
