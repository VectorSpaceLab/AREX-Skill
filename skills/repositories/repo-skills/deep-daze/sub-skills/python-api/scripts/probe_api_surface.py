#!/usr/bin/env python3
"""Probe the installed deep-daze Python API without constructing Imagine.

The probe imports deep_daze, checks signatures/defaults and helper behavior, and
optionally exits nonzero on mismatch. It deliberately avoids Imagine(...) so it
will not trigger CLIP model loading or generation.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import json
import sys
from typing import Any, Dict, List, Tuple

EXPECTED_IMAGINE_DEFAULTS: Dict[str, Any] = {
    "text": None,
    "img": None,
    "clip_encoding": None,
    "lr": 1e-5,
    "batch_size": 4,
    "gradient_accumulate_every": 4,
    "save_every": 100,
    "image_width": 512,
    "num_layers": 16,
    "epochs": 20,
    "iterations": 1050,
    "save_progress": True,
    "seed": None,
    "open_folder": True,
    "save_date_time": False,
    "start_image_path": None,
    "start_image_train_iters": 10,
    "start_image_lr": 3e-4,
    "theta_initial": None,
    "theta_hidden": None,
    "model_name": "ViT-B/32",
    "lower_bound_cutout": 0.1,
    "upper_bound_cutout": 1.0,
    "saturate_bound": False,
    "averaging_weight": 0.3,
    "create_story": False,
    "story_start_words": 5,
    "story_words_per_epoch": 5,
    "story_separator": None,
    "gauss_sampling": False,
    "gauss_mean": 0.6,
    "gauss_std": 0.2,
    "do_cutout": True,
    "center_bias": False,
    "center_focus": 2,
    "optimizer": "AdamP",
    "jit": True,
    "hidden_size": 256,
    "save_gif": False,
    "save_video": False,
}

EXPECTED_DEEPDAZE_DEFAULTS: Dict[str, Any] = {
    "num_layers": 8,
    "image_width": 512,
    "loss_coef": 100,
    "theta_initial": None,
    "theta_hidden": None,
    "lower_bound_cutout": 0.1,
    "upper_bound_cutout": 1.0,
    "saturate_bound": False,
    "gauss_sampling": False,
    "gauss_mean": 0.6,
    "gauss_std": 0.2,
    "do_cutout": True,
    "center_bias": False,
    "center_focus": 2,
    "hidden_size": 256,
    "averaging_weight": 0.3,
}

EXPECTED_MODELS = ["RN50", "RN101", "RN50x4", "ViT-B/32", "ViT-L/14"]
EXPECTED_HELPER_RESULTS = {
    "text": "a_house",
    "separator": "scene_one_",
    "img_string": "input_image",
    "img_object": "PIL_img",
    "encoding": "your_encoding",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Probe deep-daze API signatures and helpers without constructing Imagine."
    )
    p.add_argument(
        "--verify",
        action="store_true",
        help="exit nonzero if signatures/defaults/helper behavior differ from expected values",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of a compact text report",
    )
    p.add_argument(
        "--skip-tokenize",
        action="store_true",
        help="skip the tokenize('a house') shape probe",
    )
    return p


def import_api():
    import deep_daze  # noqa: F401
    from deep_daze import DeepDaze, Imagine
    from deep_daze.clip import available_models, tokenize
    from deep_daze.deep_daze import create_text_path

    return deep_daze, DeepDaze, Imagine, available_models, tokenize, create_text_path


def defaults_from_signature(obj: Any) -> Tuple[str, Dict[str, Any], List[str]]:
    sig = inspect.signature(obj)
    defaults: Dict[str, Any] = {}
    required: List[str] = []
    for name, param in sig.parameters.items():
        if param.default is inspect._empty:
            required.append(name)
        else:
            defaults[name] = param.default
    return str(sig), defaults, required


def compare_defaults(actual: Dict[str, Any], expected: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key, expected_value in expected.items():
        if key not in actual:
            errors.append(f"missing default for {key!r}")
        elif actual[key] != expected_value:
            errors.append(
                f"default mismatch for {key!r}: expected {expected_value!r}, got {actual[key]!r}"
            )
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        errors.append(f"unexpected defaulted parameters: {unexpected!r}")
    return errors


def build_report(skip_tokenize: bool) -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    deep_daze, DeepDaze, Imagine, available_models, tokenize, create_text_path = import_api()

    imagine_sig, imagine_defaults, imagine_required = defaults_from_signature(Imagine)
    deepdaze_sig, deepdaze_defaults, deepdaze_required = defaults_from_signature(DeepDaze)

    errors.extend(f"Imagine: {err}" for err in compare_defaults(imagine_defaults, EXPECTED_IMAGINE_DEFAULTS))
    errors.extend(f"DeepDaze: {err}" for err in compare_defaults(deepdaze_defaults, EXPECTED_DEEPDAZE_DEFAULTS))

    models = available_models()
    if models != EXPECTED_MODELS:
        errors.append(f"available models mismatch: expected {EXPECTED_MODELS!r}, got {models!r}")

    helper_results = {
        "text": create_text_path(77, text="a house"),
        "separator": create_text_path(77, text="scene one | scene two", separator="|"),
        "img_string": create_text_path(77, img="input image.png"),
        "img_object": create_text_path(77, img=object()),
        "encoding": create_text_path(77, encoding=object()),
    }
    if helper_results != EXPECTED_HELPER_RESULTS:
        errors.append(
            f"create_text_path behavior mismatch: expected {EXPECTED_HELPER_RESULTS!r}, got {helper_results!r}"
        )

    token_shape = None
    if not skip_tokenize:
        token_shape = tuple(tokenize("a house").shape)
        if token_shape != (1, 77):
            errors.append(f"tokenize('a house') shape mismatch: expected (1, 77), got {token_shape!r}")

    try:
        distribution_version = metadata.version("deep-daze")
    except metadata.PackageNotFoundError:
        distribution_version = None
        errors.append("distribution metadata for 'deep-daze' was not found")

    report: Dict[str, Any] = {
        "distribution": "deep-daze",
        "distribution_version": distribution_version,
        "module_version": getattr(deep_daze, "__version__", None),
        "exports": {
            "Imagine": hasattr(deep_daze, "Imagine"),
            "DeepDaze": hasattr(deep_daze, "DeepDaze"),
        },
        "imagine_signature": imagine_sig,
        "imagine_required_parameters": imagine_required,
        "imagine_defaults": imagine_defaults,
        "deepdaze_signature": deepdaze_sig,
        "deepdaze_required_parameters": deepdaze_required,
        "deepdaze_defaults": deepdaze_defaults,
        "available_models": models,
        "tokenize_a_house_shape": token_shape,
        "create_text_path": helper_results,
        "constructed_imagine": False,
        "errors": errors,
    }
    return report, errors


def print_text_report(report: Dict[str, Any]) -> None:
    print(f"distribution: {report['distribution']} {report['distribution_version']}")
    print(f"exports: Imagine={report['exports']['Imagine']} DeepDaze={report['exports']['DeepDaze']}")
    print(f"Imagine signature: {report['imagine_signature']}")
    print(f"DeepDaze signature: {report['deepdaze_signature']}")
    print(f"available models: {', '.join(report['available_models'])}")
    if report["tokenize_a_house_shape"] is not None:
        print(f"tokenize('a house') shape: {tuple(report['tokenize_a_house_shape'])}")
    print(f"create_text_path probes: {report['create_text_path']}")
    print("constructed Imagine: False")
    if report["errors"]:
        print("errors:")
        for err in report["errors"]:
            print(f"- {err}")
    else:
        print("status: ok")


def main(argv: List[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report, errors = build_report(skip_tokenize=args.skip_tokenize)
    except Exception as exc:  # import/dependency failures should be explicit and concise
        if args.json:
            print(json.dumps({"imported": False, "error": repr(exc)}, indent=2, sort_keys=True))
        else:
            print(f"deep-daze API probe failed before completion: {exc!r}", file=sys.stderr)
        return 1 if args.verify else 0

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=repr))
    else:
        print_text_report(report)

    if args.verify and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
