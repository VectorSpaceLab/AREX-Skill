#!/usr/bin/env python3
"""Safe LTX-2 core API inspector.

This helper imports installed LTX-2 packages, prints function/class signatures,
and can run tiny CPU-only shape checks. It never downloads models, never loads
checkpoint tensor payloads by default, and never runs generation or training.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_ADDR_RE = re.compile(r" at 0x[0-9a-fA-F]+")


@dataclass(frozen=True)
class ObjectSpec:
    module: str
    attr: str
    methods: tuple[str, ...] = ()
    optional: bool = False

    @property
    def key(self) -> str:
        return f"{self.module}:{self.attr}"


DEFAULT_OBJECTS: tuple[ObjectSpec, ...] = (
    ObjectSpec("ltx_core.components.schedulers", "LTX2Scheduler", ("execute",)),
    ObjectSpec("ltx_core.components.schedulers", "LinearQuadraticScheduler", ("execute",)),
    ObjectSpec("ltx_core.components.schedulers", "BetaScheduler", ("execute",)),
    ObjectSpec("ltx_core.components.guiders", "CFGGuider", ("delta", "enabled")),
    ObjectSpec("ltx_core.components.guiders", "STGGuider", ("delta", "enabled")),
    ObjectSpec("ltx_core.components.guiders", "LtxAPGGuider", ("delta", "enabled")),
    ObjectSpec("ltx_core.components.guiders", "MultiModalGuiderParams"),
    ObjectSpec("ltx_core.components.guiders", "MultiModalGuiderFactory", ("constant", "from_dict", "params", "build_from_sigma")),
    ObjectSpec("ltx_core.components.noisers", "GaussianNoiser", ("__call__",)),
    ObjectSpec("ltx_core.components.patchifiers", "VideoLatentPatchifier", ("patchify", "unpatchify", "get_token_count", "get_patch_grid_bounds")),
    ObjectSpec("ltx_core.components.patchifiers", "AudioPatchifier", ("patchify", "unpatchify", "get_token_count", "get_patch_grid_bounds")),
    ObjectSpec("ltx_core.components.patchifiers", "get_pixel_coords"),
    ObjectSpec("ltx_core.types", "VideoPixelShape"),
    ObjectSpec("ltx_core.types", "VideoLatentShape", ("from_pixel_shape", "from_torch_shape", "to_torch_shape", "token_count", "upscale")),
    ObjectSpec("ltx_core.types", "AudioLatentShape", ("from_duration", "from_video_pixel_shape", "from_torch_shape", "to_torch_shape", "token_count")),
    ObjectSpec("ltx_core.types", "LatentState", ("clone",)),
    ObjectSpec("ltx_core.tools", "VideoLatentTools", ("create_initial_state", "patchify", "unpatchify", "clear_conditioning")),
    ObjectSpec("ltx_core.tools", "AudioLatentTools", ("create_initial_state", "patchify", "unpatchify", "clear_conditioning")),
    ObjectSpec("ltx_core.conditioning", "VideoConditionByReferenceLatent"),
    ObjectSpec("ltx_core.conditioning", "VideoConditionByKeyframeIndex"),
    ObjectSpec("ltx_core.conditioning", "VideoConditionByLatentIndex"),
    ObjectSpec("ltx_core.conditioning", "VideoConditionByMask"),
    ObjectSpec("ltx_core.conditioning", "AudioConditionByReferenceLatent"),
    ObjectSpec("ltx_core.conditioning", "ConditioningItemAttentionStrengthWrapper"),
    ObjectSpec("ltx_core.conditioning", "VideoGeneratedKeyframeSlots"),
    ObjectSpec("ltx_core.loader", "SingleGPUModelBuilder", ("build", "lora", "with_sd_ops", "with_module_ops", "with_loras", "with_registry", "with_lora_load_device", "with_fuse_rule", "model_config", "model_metadata", "meta_model", "load_sd")),
    ObjectSpec("ltx_core.loader", "SDOps", ("with_replacement", "with_matching", "with_additional_allowed_keys", "with_kv_operation", "apply_to_key", "apply_to_key_value")),
    ObjectSpec("ltx_core.loader", "LoraPathStrengthAndSDOps"),
    ObjectSpec("ltx_core.loader", "ModuleOps"),
    ObjectSpec("ltx_core.model.transformer", "LTXModelConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.transformer", "LTXVideoOnlyModelConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.transformer", "LTXAudioOnlyModelConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.transformer", "Modality", ("split",)),
    ObjectSpec("ltx_core.model.video_vae", "VideoEncoderConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.video_vae", "VideoDecoderConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.audio_vae", "AudioEncoderConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.audio_vae", "AudioDecoderConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.model.audio_vae", "VocoderConfigurator", ("from_metadata",)),
    ObjectSpec("ltx_core.block_streaming", "StreamingModelBuilder", ("build", "with_sd_ops", "with_module_ops", "with_loras", "with_registry", "with_fuse_rule")),
    ObjectSpec("ltx_core.block_streaming", "BlockStreamingWrapper", ("teardown",)),
    ObjectSpec("ltx_core.quantization.policy", "QuantizationPolicy"),
    ObjectSpec("ltx_core.quantization.fp8_cast", "build_policy"),
    ObjectSpec("ltx_core.quantization.fp8_scaled_mm", "build_policy"),
    ObjectSpec("ltx_pipelines.utils.model_paths", "ModelPaths", ("from_monolith", "from_split", "transformer", "text_encoder", "video_vae", "audio_vae", "duration_head")),
    ObjectSpec("ltx_pipelines.utils.model_paths", "model_paths_from_namespace"),
    ObjectSpec("ltx_pipelines.utils.media_io", "HDRColorSpace", optional=True),
    ObjectSpec("ltx_pipelines.utils.media_io", "ResizeMode", optional=True),
    ObjectSpec("ltx_pipelines.utils.media_io", "get_videostream_metadata", optional=True),
    ObjectSpec("ltx_pipelines.utils.media_io", "align_resolution", optional=True),
    ObjectSpec("ltx_core.hdr", "HDRTransfer", ("to_working_space", "to_linear"), optional=True),
)

PIPELINE_OBJECTS: tuple[ObjectSpec, ...] = (
    ObjectSpec("ltx_pipelines.distilled", "DistilledPipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.ti2vid_two_stages", "TI2VidTwoStagesPipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.ti2vid_one_stage", "TI2VidOneStagePipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.t2a_one_stage", "T2AOneStagePipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.a2vid_two_stage", "A2VidPipelineTwoStage", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.dfr_pipeline", "DFRPipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.keyframe_interpolation", "KeyframeInterpolationPipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.ic_lora", "ICLoraPipeline", ("__call__",), optional=True),
    ObjectSpec("ltx_pipelines.retake", "RetakePipeline", ("__call__",), optional=True),
)


@dataclass
class InspectionResult:
    imports: dict[str, dict[str, Any]] = field(default_factory=dict)
    objects: dict[str, dict[str, Any]] = field(default_factory=dict)
    tiny_shapes: dict[str, Any] | None = None
    checkpoint_metadata: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _clean_signature(text: str) -> str:
    return _ADDR_RE.sub(" at 0x...", text)


def _signature(obj: Any) -> str:
    return _clean_signature(str(inspect.signature(obj)))


def _short_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _resolve_object(module_name: str, attr_path: str) -> tuple[Any, str]:
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj, getattr(obj, "__qualname__", getattr(obj, "__name__", attr_path))


def inspect_spec(spec: ObjectSpec, result: InspectionResult) -> None:
    try:
        module = importlib.import_module(spec.module)
        result.imports.setdefault(spec.module, {"ok": True})
    except Exception as exc:  # noqa: BLE001 - report import diagnostics without crashing by default
        message = f"import {spec.module}: {_short_error(exc)}"
        result.imports[spec.module] = {"ok": False, "error": _short_error(exc), "optional": spec.optional}
        if not spec.optional:
            result.errors.append(message)
        result.objects[spec.key] = {"ok": False, "error": message, "optional": spec.optional}
        return

    try:
        obj: Any = module
        for part in spec.attr.split("."):
            obj = getattr(obj, part)
        entry: dict[str, Any] = {
            "ok": True,
            "module": getattr(obj, "__module__", spec.module),
            "qualname": getattr(obj, "__qualname__", getattr(obj, "__name__", spec.attr)),
            "signature": _signature(obj),
            "optional": spec.optional,
        }
        methods: dict[str, str] = {}
        for method_name in spec.methods:
            try:
                methods[method_name] = _signature(getattr(obj, method_name))
            except Exception as exc:  # noqa: BLE001
                methods[method_name] = f"ERROR {_short_error(exc)}"
        if methods:
            entry["methods"] = methods
        result.objects[spec.key] = entry
    except Exception as exc:  # noqa: BLE001
        message = f"object {spec.key}: {_short_error(exc)}"
        result.objects[spec.key] = {"ok": False, "error": message, "optional": spec.optional}
        if not spec.optional:
            result.errors.append(message)


def parse_object_spec(raw: str) -> ObjectSpec:
    if ":" not in raw:
        raise argparse.ArgumentTypeError("object must be MODULE:ATTR, for example ltx_core.loader:SingleGPUModelBuilder")
    module, attr = raw.split(":", 1)
    module = module.strip()
    attr = attr.strip()
    if not module or not attr:
        raise argparse.ArgumentTypeError("object must include both MODULE and ATTR")
    return ObjectSpec(module, attr)


def run_tiny_shapes() -> dict[str, Any]:
    import torch

    from ltx_core.components.patchifiers import AudioPatchifier, VideoLatentPatchifier
    from ltx_core.conditioning import VideoGeneratedKeyframeSlots
    from ltx_core.tools import AudioLatentTools, VideoLatentTools
    from ltx_core.types import AudioLatentShape, VideoLatentShape, VideoPixelShape

    pixel = VideoPixelShape(batch=1, frames=33, height=512, width=768, fps=24.0)
    video_shape = VideoLatentShape.from_pixel_shape(pixel)
    audio_shape = AudioLatentShape.from_video_pixel_shape(pixel)

    video_tools = VideoLatentTools(VideoLatentPatchifier(1), video_shape, fps=pixel.fps)
    audio_tools = AudioLatentTools(AudioPatchifier(1), audio_shape)

    video_state = video_tools.create_initial_state(device="cpu", dtype=torch.float32)
    audio_state = audio_tools.create_initial_state(device="cpu", dtype=torch.float32)

    assert tuple(video_shape.to_torch_shape()) == (1, 128, 5, 16, 24)
    assert tuple(video_state.latent.shape) == (1, video_shape.token_count(), 128)
    assert tuple(video_state.positions.shape) == (1, 3, video_shape.token_count(), 2)
    assert video_state.keyframes_mask is not None
    assert tuple(video_state.keyframes_mask.shape) == (1, video_shape.token_count(), 1)
    assert tuple(audio_state.latent.shape) == (1, audio_shape.frames, 128)
    assert tuple(audio_state.positions.shape) == (1, 1, audio_shape.frames, 2)

    slots = VideoGeneratedKeyframeSlots([8, 16])
    slotted = slots.apply_to(video_state, video_tools)
    assert slotted.generated_keyframe_layout is not None
    assert slotted.generated_keyframe_layout.num_keyframes == 2
    assert slotted.generated_keyframe_layout.tokens_per_keyframe == video_tools.tokens_per_latent_frame

    return {
        "ok": True,
        "video_pixel_shape": pixel._asdict(),
        "video_latent_shape": video_shape._asdict(),
        "audio_latent_shape": audio_shape._asdict(),
        "video_tokens": video_shape.token_count(),
        "audio_tokens": audio_shape.token_count(),
        "video_state": {
            "latent": list(video_state.latent.shape),
            "positions": list(video_state.positions.shape),
            "denoise_mask": list(video_state.denoise_mask.shape),
            "keyframes_mask": list(video_state.keyframes_mask.shape),
        },
        "audio_state": {
            "latent": list(audio_state.latent.shape),
            "positions": list(audio_state.positions.shape),
            "denoise_mask": list(audio_state.denoise_mask.shape),
        },
        "generated_keyframe_slots": {
            "pixel_frame_indices": list(slotted.generated_keyframe_layout.pixel_frame_indices),
            "tokens_per_keyframe": slotted.generated_keyframe_layout.tokens_per_keyframe,
            "first_token": slotted.generated_keyframe_layout.first_token,
            "total_tokens_after_slots": int(slotted.latent.shape[1]),
        },
    }


def inspect_checkpoint_metadata(path: str) -> dict[str, Any]:
    from ltx_core.loader import SafetensorsModelStateDictLoader

    loader = SafetensorsModelStateDictLoader()
    metadata = loader.metadata(path)
    config = metadata.get("config", {}) if isinstance(metadata, dict) else {}
    transformer = config.get("transformer", {}) if isinstance(config, dict) else {}
    vae = config.get("vae", {}) if isinstance(config, dict) else {}

    tensor_count: int | None = None
    try:
        import safetensors

        with safetensors.safe_open(path, framework="pt") as handle:
            tensor_count = len(list(handle.keys()))
    except Exception:
        tensor_count = None

    return {
        "ok": True,
        "path_name": Path(path).name,
        "metadata_keys": sorted(str(k) for k in metadata.keys()),
        "config_sections": sorted(str(k) for k in config.keys()) if isinstance(config, dict) else [],
        "model_version": metadata.get("model_version"),
        "vae_class_name": vae.get("_class_name") if isinstance(vae, dict) else None,
        "transformer_use_keyframes_abs_pos_embedding": (
            transformer.get("use_keyframes_abs_pos_embedding") if isinstance(transformer, dict) else None
        ),
        "tensor_count": tensor_count,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect installed LTX-2 core APIs and selected shape contracts. "
            "No model downloads, generation, training, or checkpoint tensor loading are performed."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any required import/object check fails.")
    parser.add_argument("--include-pipelines", action="store_true", help="Also inspect selected high-level pipeline constructors and __call__ signatures.")
    parser.add_argument("--tiny-shapes", action="store_true", help="Run CPU-only tensor shape checks for latent tools and generated keyframe slots.")
    parser.add_argument("--list-objects", action="store_true", help="List built-in object specs and exit.")
    parser.add_argument(
        "--object",
        dest="objects",
        action="append",
        type=parse_object_spec,
        default=[],
        metavar="MODULE:ATTR",
        help="Inspect an additional object, for example ltx_core.loader:SingleGPUModelBuilder. May be repeated.",
    )
    parser.add_argument(
        "--checkpoint-metadata",
        metavar="PATH",
        help="Read safetensors metadata/header summary for a local checkpoint/component file. Does not load tensor payloads.",
    )
    return parser


def print_text(result: InspectionResult) -> None:
    print("LTX-2 core API inspection")
    print(f"status: {'ok' if result.ok else 'completed with errors'}")
    print("\nImports:")
    for module, info in sorted(result.imports.items()):
        if info.get("ok"):
            print(f"  OK    {module}")
        else:
            opt = " optional" if info.get("optional") else ""
            print(f"  FAIL  {module}{opt}: {info.get('error')}")

    print("\nObjects:")
    for key, info in sorted(result.objects.items()):
        if not info.get("ok"):
            opt = " optional" if info.get("optional") else ""
            print(f"  FAIL  {key}{opt}: {info.get('error')}")
            continue
        print(f"  OK    {key}")
        print(f"        resolved: {info.get('module')}.{info.get('qualname')}")
        print(f"        signature: {info.get('signature')}")
        for method, sig in info.get("methods", {}).items():
            print(f"        {method}{sig}")

    if result.tiny_shapes is not None:
        print("\nTiny shape checks:")
        print(json.dumps(result.tiny_shapes, indent=2, sort_keys=True))

    if result.checkpoint_metadata is not None:
        print("\nCheckpoint metadata summary:")
        print(json.dumps(result.checkpoint_metadata, indent=2, sort_keys=True))

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    specs = list(DEFAULT_OBJECTS)
    if args.include_pipelines:
        specs.extend(PIPELINE_OBJECTS)
    specs.extend(args.objects)

    if args.list_objects:
        for spec in specs:
            suffix = " optional" if spec.optional else ""
            methods = f" methods={','.join(spec.methods)}" if spec.methods else ""
            print(f"{spec.key}{suffix}{methods}")
        return 0

    result = InspectionResult()
    for spec in specs:
        inspect_spec(spec, result)

    if args.tiny_shapes:
        try:
            result.tiny_shapes = run_tiny_shapes()
        except Exception as exc:  # noqa: BLE001
            message = f"tiny shape checks: {_short_error(exc)}"
            result.tiny_shapes = {"ok": False, "error": _short_error(exc)}
            result.errors.append(message)

    if args.checkpoint_metadata:
        try:
            result.checkpoint_metadata = inspect_checkpoint_metadata(args.checkpoint_metadata)
        except Exception as exc:  # noqa: BLE001
            message = f"checkpoint metadata: {_short_error(exc)}"
            result.checkpoint_metadata = {"ok": False, "error": _short_error(exc), "path_name": Path(args.checkpoint_metadata).name}
            result.errors.append(message)

    payload = {
        "ok": result.ok,
        "imports": result.imports,
        "objects": result.objects,
        "tiny_shapes": result.tiny_shapes,
        "checkpoint_metadata": result.checkpoint_metadata,
        "errors": result.errors,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print_text(result)

    return 1 if args.strict and not result.ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
