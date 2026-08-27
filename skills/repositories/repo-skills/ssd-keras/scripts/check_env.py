#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

EXPECTED_RUNTIME_PACKAGES = [
    "bounding_box_utils",
    "data_generator",
    "eval_utils",
    "keras_layers",
    "keras_loss_function",
    "misc_utils",
    "models",
    "ssd_encoder_decoder",
]

RUNTIME_SRC = None


def assert_bundled_module(module_name: str) -> None:
    module = sys.modules.get(module_name) or __import__(module_name)
    module_file = getattr(module, "__file__", None)
    if RUNTIME_SRC is None or module_file is None:
        raise RuntimeError(f"Cannot verify bundled location for {module_name}")
    resolved = Path(module_file).resolve()
    try:
        resolved.relative_to(RUNTIME_SRC)
    except ValueError as exc:
        raise RuntimeError(f"{module_name} imported from {resolved}, expected it under {RUNTIME_SRC}") from exc


def locate_skill_root() -> Path:
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "SKILL.md").is_file() and (parent / "runtime-src").is_dir():
            return parent
    raise FileNotFoundError("Could not locate the bundled SSD Keras skill root or its runtime-src directory.")


def add_runtime_source() -> tuple[Path, Path]:
    global RUNTIME_SRC
    skill_root = locate_skill_root()
    runtime_src = skill_root / "runtime-src"
    if str(runtime_src) not in sys.path:
        sys.path.insert(0, str(runtime_src))
    RUNTIME_SRC = runtime_src.resolve()
    return skill_root, runtime_src


def report_module(name: str) -> str:
    module = __import__(name)
    version = getattr(module, "__version__", "unknown")
    return f"{name} {version}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quick environment and import smoke for the bundled SSD Keras skill."
    )
    parser.parse_args()

    skill_root, runtime_src = add_runtime_source()
    print(f"skill-root: {skill_root}")
    print(f"runtime-source: {runtime_src}")
    print(f"python: {sys.version.split()[0]}")

    missing = [name for name in EXPECTED_RUNTIME_PACKAGES if not (runtime_src / name).exists()]
    if missing:
        print(f"runtime source missing required packages: {', '.join(missing)}")
        return 1

    for name in ["tensorflow", "keras", "cv2", "bs4", "h5py", "sklearn", "imageio", "matplotlib"]:
        try:
            print(report_module(name))
        except Exception as exc:  # pragma: no cover - smoke script
            print(f"{name} import failed: {type(exc).__name__}: {exc}")
            return 1

    try:
        import keras
        from models.keras_ssd300 import ssd_300
        from models.keras_ssd512 import ssd_512
        from models.keras_ssd7 import build_model
        from data_generator.object_detection_2d_data_generator import DataGenerator
        from ssd_encoder_decoder.ssd_input_encoder import SSDInputEncoder
        from ssd_encoder_decoder.ssd_output_decoder import decode_detections, decode_detections_fast
        from eval_utils.average_precision_evaluator import Evaluator
        from keras_loss_function.keras_ssd_loss import SSDLoss
        from misc_utils.tensor_sampling_utils import sample_tensors
    except Exception as exc:  # pragma: no cover - smoke script
        print(f"runtime import failed: {type(exc).__name__}: {exc}")
        return 1

    for package_name in EXPECTED_RUNTIME_PACKAGES:
        assert_bundled_module(package_name)
    print("runtime imports verified under bundled runtime-src")

    print(f"keras-backend: {keras.backend.backend()}")
    for label, obj in [
        ("ssd_300", ssd_300),
        ("ssd_512", ssd_512),
        ("build_model", build_model),
        ("DataGenerator.generate", DataGenerator.generate),
        ("SSDInputEncoder", SSDInputEncoder.__init__),
        ("decode_detections", decode_detections),
        ("decode_detections_fast", decode_detections_fast),
        ("Evaluator.__call__", Evaluator.__call__),
        ("SSDLoss.compute_loss", SSDLoss.compute_loss),
        ("sample_tensors", sample_tensors),
    ]:
        try:
            print(f"{label}: {inspect.signature(obj)}")
        except Exception as exc:  # pragma: no cover - smoke script
            print(f"{label}: signature unavailable ({type(exc).__name__}: {exc})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
