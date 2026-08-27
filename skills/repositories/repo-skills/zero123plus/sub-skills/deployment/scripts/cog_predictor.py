#!/usr/bin/env python3
"""Zero123Plus Cog predictor template.

This file is a clean-room deployment wrapper derived from the repo's Cog
predictor behavior. It does not load models on import, makes cache/model paths
configurable, and keeps automatic downloads opt-in so future agents can adapt it
safely for new container layouts.

The detailed image-to-multiview generation workflow belongs to the sibling
generation sub-skill; this template only preserves the deployment-facing
prediction contract.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path as LocalPath
from typing import List

try:
    from cog import BasePredictor, Input, Path
    _COG_IMPORT_ERROR = None
except ImportError as exc:  # pragma: no cover - only exercised outside Cog.
    _COG_IMPORT_ERROR = exc

    class BasePredictor:  # type: ignore[override]
        """Fallback base so the module can still be imported for inspection."""

        pass

    def Input(*args, **kwargs):  # type: ignore[override]
        return kwargs.get("default")

    Path = LocalPath  # type: ignore[assignment]


DEFAULT_WEIGHTS_DIR = LocalPath(
    os.environ.get("ZERO123PLUS_WEIGHTS_DIR", "./weights/zero123plusplus")
).expanduser()
DEFAULT_TMP_DIR = LocalPath(
    os.environ.get("ZERO123PLUS_TMP_DIR", "./tmp/zero123plus-cog")
).expanduser()
DEFAULT_OUTPUT_DIR = LocalPath(
    os.environ.get("ZERO123PLUS_OUTPUT_DIR", tempfile.gettempdir())
).expanduser()
DEFAULT_MODEL_SOURCE = os.environ.get("ZERO123PLUS_MODEL_SOURCE")
DEFAULT_CUSTOM_PIPELINE = os.environ.get(
    "ZERO123PLUS_CUSTOM_PIPELINE", "sudo-ai/zero123plus-pipeline"
)
DEFAULT_WEIGHTS_URL = os.environ.get(
    "ZERO123PLUS_WEIGHTS_URL",
    "https://weights.replicate.delivery/default/zero123plusplus/zero123plusplus.tar",
)
ALLOW_DOWNLOAD = os.environ.get("ZERO123PLUS_ALLOW_DOWNLOAD", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CUDA_DEVICE = os.environ.get("ZERO123PLUS_DEVICE", "cuda:0")


def _ensure_cog() -> None:
    if _COG_IMPORT_ERROR is not None:
        raise ImportError(
            "The cog package is not installed. Run this template under Cog or "
            "install cog before importing the predictor."
        ) from _COG_IMPORT_ERROR


def _require_import(module_name: str, install_hint: str):
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise ImportError(
            f"Missing required dependency '{module_name}'. Install it with: {install_hint}"
        ) from exc


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _find_extracted_root(tmp_dir: LocalPath) -> LocalPath:
    direct = tmp_dir / "zero123plusplus"
    if direct.exists():
        return direct
    for model_index in tmp_dir.rglob("model_index.json"):
        return model_index.parent
    raise RuntimeError(
        "pget finished but no Diffusers model tree was found in the temporary \
extraction directory."
    )


def _download_weights(weights_url: str, weights_dir: LocalPath, tmp_dir: LocalPath) -> None:
    pget_path = shutil.which("pget")
    if pget_path is None:
        raise RuntimeError(
            "pget is not installed, so the weight archive cannot be fetched. \
Install pget in the Cog image or pre-populate the weights directory."
        )

    tmp_dir.mkdir(parents=True, exist_ok=True)
    if tmp_dir.exists():
        for child in tmp_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    print(f"Downloading Zero123Plus weights from {weights_url} ...")
    subprocess.run([pget_path, "-x", weights_url, str(tmp_dir)], check=True)

    extracted_root = _find_extracted_root(tmp_dir)
    if weights_dir.exists():
        shutil.rmtree(weights_dir)
    weights_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(extracted_root), str(weights_dir))


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory for repeated Cog predictions."""

        _ensure_cog()
        torch = _require_import("torch", "pip install torch==2.0.1 torchvision==0.15.2")
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is not available. The Zero123Plus Cog predictor is GPU-only \
and expects a CUDA-enabled torch build."
            )

        # The source predictor downloaded to a fixed container cache. This template
        # replaces that hard-coded path with configurable environment-driven paths.
        if DEFAULT_MODEL_SOURCE:
            model_source = DEFAULT_MODEL_SOURCE
        else:
            model_source = str(DEFAULT_WEIGHTS_DIR)
            if not DEFAULT_WEIGHTS_DIR.exists():
                if not ALLOW_DOWNLOAD:
                    raise RuntimeError(
                        "Zero123Plus weights are missing and automatic download is disabled. \
Set ZERO123PLUS_ALLOW_DOWNLOAD=1 or pre-populate ZERO123PLUS_WEIGHTS_DIR."
                    )
                _download_weights(DEFAULT_WEIGHTS_URL, DEFAULT_WEIGHTS_DIR, DEFAULT_TMP_DIR)

        allow_hf_download = ALLOW_DOWNLOAD or _env_bool("ZERO123PLUS_ALLOW_HF_DOWNLOAD", False)
        local_files_only = not allow_hf_download

        _require_import(
            "diffusers",
            "pip install diffusers==0.20.2 transformers==4.29.2",
        )
        # Keep the import check visible for helpful errors, but use a direct import for the API.
        from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler

        try:
            self.pipeline = DiffusionPipeline.from_pretrained(
                model_source,
                custom_pipeline=DEFAULT_CUSTOM_PIPELINE,
                torch_dtype=torch.float16,
                local_files_only=local_files_only,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to load the Zero123Plus pipeline. If the custom pipeline or \
model cache is not already present, either pre-stage it or allow downloads via \
ZERO123PLUS_ALLOW_DOWNLOAD / ZERO123PLUS_ALLOW_HF_DOWNLOAD."
            ) from exc

        self.pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
            self.pipeline.scheduler.config,
            timestep_spacing="trailing",
        )
        self.pipeline.to(CUDA_DEVICE)
        self._rembg_session = None
        self._output_dir = DEFAULT_OUTPUT_DIR
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def predict(
        self,
        image: Path = Input(
            description="Input image. Aspect ratio should be 1:1. Recommended resolution is >= 320x320 pixels.",
        ),
        remove_background: bool = Input(
            description="Remove the background of the input image",
            default=False,
        ),
        return_intermediate_images: bool = Input(
            description="Return the intermediate images together with the output images",
            default=False,
        ),
    ) -> List[Path]:
        """Run one Zero123Plus prediction and return the saved outputs."""

        _ensure_cog()
        if not hasattr(self, "pipeline"):
            raise RuntimeError("Predictor.setup() must be called before predict().")

        _require_import("PIL.Image", "pip install pillow")
        from PIL import Image

        cond = Image.open(str(image))
        source_path = LocalPath(str(image))
        image_name = f"original{source_path.suffix or '.png'}"

        if remove_background:
            rembg = _require_import(
                "rembg",
                "pip install rembg==2.0.51 onnxruntime",
            )
            if self._rembg_session is None:
                self._rembg_session = rembg.new_session()
            cond = rembg.remove(cond, session=self._rembg_session)
            image_name = f"{source_path.stem}.png"

        outputs: List[LocalPath] = []
        if return_intermediate_images:
            temp_original = self._output_dir / image_name
            cond.save(temp_original)
            outputs.append(temp_original)

        all_results = self.pipeline(cond, num_inference_steps=75)
        for i, output_img in enumerate(all_results.images):
            filename = self._output_dir / f"output_{i}.jpg"
            output_img.save(filename)
            outputs.append(filename)

        return [Path(str(output)) for output in outputs]


if __name__ == "__main__":
    if _COG_IMPORT_ERROR is not None:
        print(
            "This file is a Cog predictor template. Install cog and run it with the \
Cog CLI, or import it only for inspection."
        )
    else:
        print(
            "This file is meant for Cog. Configure ZERO123PLUS_* environment \
variables to choose a weights directory, model source, and download policy."
        )
