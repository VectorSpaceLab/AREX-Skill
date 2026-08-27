#!/usr/bin/env python3
"""No-download smoke checks for Optimum utility/config APIs.

The script builds tiny in-memory configs, checks NormalizedConfig.with_args,
generates text/vision/label dummy inputs, and optionally verifies BaseConfig
save/load in a temporary directory. It never downloads models or datasets.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Tuple


def _tensor_shape(value: Any) -> Tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is None:
        raise AssertionError(f"object has no shape attribute: {type(value)!r}")
    return tuple(int(dim) for dim in shape)


def _tensor_dtype(value: Any) -> str:
    return str(getattr(value, "dtype", type(value).__name__))


def _assert_shape(name: str, value: Any, expected: Iterable[int]) -> None:
    actual = _tensor_shape(value)
    expected_tuple = tuple(expected)
    if actual != expected_tuple:
        raise AssertionError(f"{name} shape mismatch: expected {expected_tuple}, got {actual}")


def _assert_dtype_contains(name: str, value: Any, expected_token: str) -> None:
    dtype = _tensor_dtype(value)
    if expected_token not in dtype:
        raise AssertionError(f"{name} dtype mismatch: expected token {expected_token!r}, got {dtype!r}")


def _seed(framework: str) -> None:
    random.seed(0)
    try:
        import numpy as np

        np.random.seed(0)
    except Exception:
        pass
    if framework == "pt":
        import torch

        torch.manual_seed(0)


def _check_dummy_inputs(framework: str) -> Dict[str, Any]:
    _seed(framework)

    from optimum.utils.input_generators import DummyLabelsGenerator, DummyTextInputGenerator, DummyVisionInputGenerator
    from optimum.utils.normalized_config import NormalizedTextConfig, NormalizedVisionConfig

    raw_text_config = SimpleNamespace(
        vocab_size=101,
        hidden_size=16,
        num_hidden_layers=2,
        num_attention_heads=4,
        eos_token_id=2,
        attribute_map={},
    )
    normalized_text = NormalizedTextConfig(raw_text_config)
    text_generator = DummyTextInputGenerator(
        task="text-classification",
        normalized_config=normalized_text,
        batch_size=2,
        sequence_length=5,
    )
    input_ids = text_generator.generate("input_ids", framework=framework, int_dtype="int32")
    attention_mask = text_generator.generate("attention_mask", framework=framework, int_dtype="int64")
    _assert_shape("input_ids", input_ids, (2, 5))
    _assert_shape("attention_mask", attention_mask, (2, 5))
    _assert_dtype_contains("input_ids", input_ids, "int32")

    labels_generator = DummyLabelsGenerator(
        task="text-classification",
        normalized_config=normalized_text,
        batch_size=2,
        num_labels=3,
    )
    labels = labels_generator.generate("labels", framework=framework, int_dtype="int64")
    _assert_shape("labels", labels, (2,))

    raw_vision_config = SimpleNamespace(image_size=8, num_channels=3, attribute_map={})
    normalized_vision = NormalizedVisionConfig(raw_vision_config)
    vision_generator = DummyVisionInputGenerator(
        task="image-classification",
        normalized_config=normalized_vision,
        batch_size=1,
        num_channels=3,
        height=16,
        width=16,
    )
    pixel_values = vision_generator.generate("pixel_values", framework=framework, float_dtype="fp32")
    pixel_mask = vision_generator.generate("pixel_mask", framework=framework, int_dtype="int64")
    _assert_shape("pixel_values", pixel_values, (1, 3, 8, 8))
    _assert_shape("pixel_mask", pixel_mask, (1, 8, 8))
    _assert_dtype_contains("pixel_values", pixel_values, "float32")

    return {
        "framework": framework,
        "input_ids": {"shape": _tensor_shape(input_ids), "dtype": _tensor_dtype(input_ids)},
        "attention_mask": {"shape": _tensor_shape(attention_mask), "dtype": _tensor_dtype(attention_mask)},
        "labels": {"shape": _tensor_shape(labels), "dtype": _tensor_dtype(labels)},
        "pixel_values": {"shape": _tensor_shape(pixel_values), "dtype": _tensor_dtype(pixel_values)},
        "pixel_mask": {"shape": _tensor_shape(pixel_mask), "dtype": _tensor_dtype(pixel_mask)},
    }


def _check_with_args(framework: str) -> Dict[str, Any]:
    from optimum.utils.input_generators import DummyTextInputGenerator
    from optimum.utils.normalized_config import NormalizedTextConfig

    raw = SimpleNamespace(vocab=33, dim=12, layers=2, heads=3, eos=1, attribute_map={})
    NormalizedTiny = NormalizedTextConfig.with_args(
        vocab_size="vocab",
        hidden_size="dim",
        num_layers="layers",
        num_attention_heads="heads",
        eos_token_id="eos",
    )
    normalized = NormalizedTiny(raw)
    if normalized.vocab_size != 33 or normalized.hidden_size != 12:
        raise AssertionError("NormalizedConfig.with_args did not expose expected fields")

    generator = DummyTextInputGenerator(
        task="text-classification",
        normalized_config=normalized,
        batch_size=1,
        sequence_length=4,
    )
    ids = generator.generate("input_ids", framework=framework, int_dtype="int64")
    _assert_shape("with_args input_ids", ids, (1, 4))
    return {
        "vocab_size": normalized.vocab_size,
        "hidden_size": normalized.hidden_size,
        "generated_shape": _tensor_shape(ids),
        "generated_dtype": _tensor_dtype(ids),
    }


def _check_base_config() -> Dict[str, Any]:
    from optimum.configuration_utils import BaseConfig

    class TinyOptimumConfig(BaseConfig):
        CONFIG_NAME = "tiny_optimum_config.json"
        FULL_CONFIGURATION_FILE = "tiny_optimum_config.json"
        model_type = "tiny-optimum"

        def __init__(self, width: int = 7, **kwargs: Any) -> None:
            self.width = width
            super().__init__(**kwargs)

    with tempfile.TemporaryDirectory(prefix="optimum-utils-smoke-") as tmpdir:
        config = TinyOptimumConfig(width=11)
        config.save_pretrained(tmpdir)
        expected_file = os.path.join(tmpdir, TinyOptimumConfig.CONFIG_NAME)
        if not os.path.exists(expected_file):
            raise AssertionError(f"expected config file not written: {TinyOptimumConfig.CONFIG_NAME}")
        loaded = TinyOptimumConfig.from_pretrained(tmpdir)
        if loaded.width != 11:
            raise AssertionError(f"BaseConfig round trip changed width: {loaded.width!r}")
        return {"config_name": TinyOptimumConfig.CONFIG_NAME, "width": loaded.width}


def _check_task_processors(strict: bool) -> Dict[str, Any]:
    try:
        from optimum.utils.preprocessing import TaskProcessorsManager
    except Exception as exc:  # optional dependencies can fail here.
        if strict:
            raise
        return {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}

    tasks = sorted(TaskProcessorsManager._TASK_TO_DATASET_PROCESSING_CLASS.keys())
    return {"status": "available", "tasks": tasks}


def _frameworks(value: str) -> List[str]:
    return ["pt", "np"] if value == "both" else [value]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run no-download Optimum utility/config smoke checks using tiny local configs. "
            "Checks NormalizedConfig.with_args, dummy text/vision/label inputs, and optional BaseConfig serialization."
        )
    )
    parser.add_argument(
        "--framework",
        choices=["pt", "np", "both"],
        default="both",
        help="Framework for generated dummy inputs. Default: both.",
    )
    parser.add_argument(
        "--skip-base-config",
        action="store_true",
        help="Skip the BaseConfig save/load round trip in a temporary directory.",
    )
    parser.add_argument(
        "--check-task-processors",
        action="store_true",
        help="Also try importing TaskProcessorsManager. This may reveal optional torchvision/Pillow dependency issues.",
    )
    parser.add_argument(
        "--strict-task-processors",
        action="store_true",
        help="Fail if --check-task-processors cannot import TaskProcessorsManager.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: Dict[str, Any] = {"dummy_inputs": {}}
    selected_frameworks = _frameworks(args.framework)

    try:
        for framework in selected_frameworks:
            results["dummy_inputs"][framework] = _check_dummy_inputs(framework)
        results["with_args"] = _check_with_args(selected_frameworks[0])
        if not args.skip_base_config:
            results["base_config"] = _check_base_config()
        if args.check_task_processors:
            results["task_processors"] = _check_task_processors(args.strict_task_processors)
    except Exception as exc:
        print(f"utils_smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print("Optimum utilities smoke: OK")
        for framework, info in results["dummy_inputs"].items():
            text_shape = tuple(info["input_ids"]["shape"])
            vision_shape = tuple(info["pixel_values"]["shape"])
            print(f"  {framework}: input_ids{text_shape}, pixel_values{vision_shape}")
        print(
            "  with_args: "
            f"vocab_size={results['with_args']['vocab_size']}, "
            f"hidden_size={results['with_args']['hidden_size']}"
        )
        if "base_config" in results:
            print(
                "  base_config: "
                f"{results['base_config']['config_name']} width={results['base_config']['width']}"
            )
        if "task_processors" in results:
            status = results["task_processors"].get("status")
            if status == "available":
                print("  task_processors: " + ", ".join(results["task_processors"]["tasks"]))
            else:
                print("  task_processors: unavailable (optional dependencies missing or incompatible)")
                print(f"    {results['task_processors']['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
