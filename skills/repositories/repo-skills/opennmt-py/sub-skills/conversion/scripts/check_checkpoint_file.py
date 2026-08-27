#!/usr/bin/env python3
"""Inspect an OpenNMT-py checkpoint without moving tensors to GPU.

The script reports top-level checkpoint keys, option metadata, vocabulary
availability, tensor section summaries, safetensors sidecars, and readiness hints
for OpenNMT-py averaging/release workflows.

Example:
    python scripts/check_checkpoint_file.py model.pt --json

Security note: OpenNMT-py checkpoints are PyTorch pickle files. Only inspect
trusted checkpoints or run this helper inside an appropriate sandbox.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _import_torch():
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise SystemExit(f"ERROR: could not import torch: {exc}") from exc
    return torch


def _torch_load_kwargs(torch_mod: Any, *, mmap: bool | None) -> dict[str, Any]:
    """Return kwargs accepted by the installed torch.load."""
    import inspect

    params = inspect.signature(torch_mod.load).parameters
    kwargs: dict[str, Any] = {"map_location": "cpu"}
    if "weights_only" in params:
        # OpenNMT-py checkpoints commonly contain argparse.Namespace in `opt`.
        kwargs["weights_only"] = False
    if mmap is not None and "mmap" in params:
        kwargs["mmap"] = mmap
    return kwargs


def _load_checkpoint(path: Path, allow_cpu_tensor_load: bool, no_mmap: bool) -> tuple[Any, dict[str, Any]]:
    torch = _import_torch()

    fake_mode_error: str | None = None
    try:
        from torch._subclasses.fake_tensor import FakeTensorMode  # type: ignore

        mmap_attempts: list[bool | None] = [False] if no_mmap else [True, False, None]
        errors: list[str] = []
        for mmap_value in mmap_attempts:
            try:
                with FakeTensorMode():
                    kwargs = _torch_load_kwargs(torch, mmap=mmap_value)
                    checkpoint = torch.load(str(path), **kwargs)
                return checkpoint, {
                    "mode": "fake_tensor",
                    "map_location": "cpu",
                    "mmap": kwargs.get("mmap"),
                    "tensor_data_loaded": False,
                }
            except Exception as exc:  # try another metadata-only variant
                errors.append(f"mmap={mmap_value}: {type(exc).__name__}: {exc}")
        fake_mode_error = "; ".join(errors)
    except Exception as exc:  # fake tensor support is best effort
        fake_mode_error = f"{type(exc).__name__}: {exc}"

    if not allow_cpu_tensor_load:
        raise RuntimeError(
            "fake tensor metadata load failed; retry with --allow-cpu-tensor-load "
            "only for trusted checkpoints that fit in CPU RAM. "
            f"Fake load error: {fake_mode_error}"
        )

    cpu_errors: list[str] = []
    for mmap_value in ([False] if no_mmap else [True, False, None]):
        try:
            kwargs = _torch_load_kwargs(torch, mmap=mmap_value)
            checkpoint = torch.load(str(path), **kwargs)
            return checkpoint, {
                "mode": "cpu_tensor",
                "map_location": "cpu",
                "mmap": kwargs.get("mmap"),
                "tensor_data_loaded": True,
                "fake_mode_error": fake_mode_error,
            }
        except Exception as exc:
            cpu_errors.append(f"mmap={mmap_value}: {type(exc).__name__}: {exc}")
    raise RuntimeError("CPU tensor load failed after fake load failed. " + "; ".join(cpu_errors))


def _is_tensor(obj: Any) -> bool:
    return hasattr(obj, "shape") and hasattr(obj, "dtype") and hasattr(obj, "device")


def _shape(obj: Any) -> list[int] | str:
    try:
        return list(obj.shape)
    except Exception:
        return "unknown"


def _safe_len(obj: Any) -> int | None:
    try:
        return len(obj)  # type: ignore[arg-type]
    except Exception:
        return None


def _jsonable(value: Any, max_string: int = 180) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, str) and len(value) > max_string:
            return value[: max_string - 3] + "..."
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v, max_string=max_string) for v in value[:20]]
    if isinstance(value, set):
        return sorted(_jsonable(v, max_string=max_string) for v in list(value)[:20])
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v, max_string=max_string) for k, v in list(value.items())[:50]}
    if _is_tensor(value):
        return {
            "kind": type(value).__name__,
            "shape": _shape(value),
            "dtype": str(getattr(value, "dtype", "unknown")),
            "device": str(getattr(value, "device", "unknown")),
        }
    return repr(value)[:max_string]


def _iter_tensors(obj: Any, prefix: str = ""):
    if _is_tensor(obj):
        yield prefix or "<tensor>", obj
        return
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_tensors(value, next_prefix)
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            next_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _iter_tensors(value, next_prefix)


def _tensor_summary(obj: Any, max_keys: int) -> dict[str, Any]:
    samples = []
    count = 0
    dtype_counts: dict[str, int] = {}
    device_counts: dict[str, int] = {}
    for name, tensor in _iter_tensors(obj):
        count += 1
        dtype = str(getattr(tensor, "dtype", "unknown"))
        device = str(getattr(tensor, "device", "unknown"))
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
        device_counts[device] = device_counts.get(device, 0) + 1
        if len(samples) < max_keys:
            samples.append(
                {
                    "name": name,
                    "shape": _shape(tensor),
                    "dtype": dtype,
                    "device": device,
                    "fake_tensor": type(tensor).__name__.lower().startswith("fake"),
                }
            )
    return {
        "tensor_count": count,
        "dtype_counts": dtype_counts,
        "device_counts": device_counts,
        "sample_tensors": samples,
    }


def _mapping_key_sample(obj: Any, max_keys: int) -> list[str]:
    if isinstance(obj, Mapping):
        return [str(k) for k in list(obj.keys())[:max_keys]]
    return []


def _option_summary(opt: Any) -> dict[str, Any]:
    if opt is None:
        return {"present": False}
    if isinstance(opt, Mapping):
        data = dict(opt)
    else:
        data = getattr(opt, "__dict__", {}) or {}
    important_fields = [
        "model_task",
        "model_type",
        "encoder_type",
        "decoder_type",
        "layers",
        "enc_layers",
        "dec_layers",
        "hidden_size",
        "enc_hid_size",
        "dec_hid_size",
        "word_vec_size",
        "src_word_vec_size",
        "tgt_word_vec_size",
        "heads",
        "share_vocab",
        "src_vocab_size",
        "tgt_vocab_size",
        "vocab_size_multiple",
        "decoder_start_token",
        "transforms",
        "src_subword_type",
        "tgt_subword_type",
        "src_subword_model",
        "tgt_subword_model",
        "src_subword_vocab",
        "tgt_subword_vocab",
        "model_dtype",
        "position_encoding",
        "max_relative_positions",
        "layer_norm",
        "norm_eps",
        "pos_ffn_activation_fn",
        "multiquery",
        "num_kv",
        "parallel_residual",
        "quant_layers",
        "quant_type",
        "lora_layers",
        "lora_rank",
        "lora_alpha",
        "lora_dropout",
        "lora_embedding",
    ]
    selected = {field: _jsonable(data[field]) for field in important_fields if field in data}
    return {
        "present": True,
        "type": type(opt).__name__,
        "field_count": len(data),
        "selected_fields": selected,
        "sample_fields": {str(k): _jsonable(v) for k, v in list(data.items())[:20]},
    }


def _vocab_side_summary(value: Any, max_items: int) -> dict[str, Any]:
    length = _safe_len(value)
    sample: list[Any] = []
    if isinstance(value, Mapping):
        sample = list(value.keys())[:max_items]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sample = list(value[:max_items])
    elif hasattr(value, "ids_to_tokens"):
        try:
            sample = list(value.ids_to_tokens[:max_items])
        except Exception:
            sample = []
    elif hasattr(value, "get_itos"):
        try:
            sample = list(value.get_itos()[:max_items])
        except Exception:
            sample = []
    return {"type": type(value).__name__, "length": length, "sample": [_jsonable(x) for x in sample]}


def _vocab_summary(vocab: Any, max_items: int) -> dict[str, Any]:
    if vocab is None:
        return {"present": False}
    if isinstance(vocab, Mapping):
        sides = {str(k): _vocab_side_summary(v, max_items) for k, v in vocab.items()}
        return {"present": True, "type": type(vocab).__name__, "sides": sides}
    return {"present": True, "type": type(vocab).__name__, "value": _vocab_side_summary(vocab, max_items)}


def _find_sidecars(path: Path) -> list[str]:
    parent = path.parent if path.parent != Path("") else Path(".")
    stem = path.name[:-3] if path.name.endswith(".pt") else path.name
    patterns = [f"{stem}.*.safetensors", f"{path.name}.*.safetensors"]
    sidecars: list[str] = []
    for pattern in patterns:
        for match in sorted(parent.glob(pattern)):
            if match.is_file():
                sidecars.append(match.name)
    return sorted(set(sidecars))


def _contains_lora(obj: Any) -> bool:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if "lora" in str(key).lower():
                return True
            if _contains_lora(value):
                return True
    elif isinstance(obj, (list, tuple)):
        return any(_contains_lora(x) for x in obj)
    return False


def _conversion_readiness(checkpoint: Any, opt_summary: dict[str, Any], sidecars: list[str]) -> dict[str, Any]:
    if not isinstance(checkpoint, Mapping):
        return {
            "average_models": {"ready": False, "missing": ["top-level checkpoint is not a mapping"]},
            "release_model": {"ready": False, "missing": ["top-level checkpoint is not a mapping"]},
            "lora": {"candidate": False},
        }
    keys = set(str(k) for k in checkpoint.keys())
    average_required = {"model", "generator", "vocab", "opt"}
    release_required = {"model", "generator", "vocab", "opt"}
    selected = opt_summary.get("selected_fields", {}) if isinstance(opt_summary, Mapping) else {}
    lora_fields = [k for k in selected.keys() if str(k).startswith("lora_")]
    lora_in_tensors = _contains_lora(checkpoint.get("model")) or _contains_lora(checkpoint.get("generator"))
    return {
        "average_models": {
            "ready": average_required.issubset(keys),
            "missing": sorted(average_required - keys),
            "note": "All averaged checkpoints must also share matching model/generator keys, vocab, and options.",
        },
        "release_model": {
            "ready": release_required.issubset(keys),
            "missing": sorted(release_required - keys),
            "optim_present": "optim" in keys and checkpoint.get("optim") is not None,
        },
        "ctranslate2_release": {
            "candidate": release_required.issubset(keys),
            "requires_dependency": "ctranslate2",
            "quantization_choices": ["int8", "int16", "float16", "int8_float16"],
        },
        "lora": {
            "candidate": bool(lora_fields or lora_in_tensors),
            "option_fields": lora_fields,
            "lora_tensor_keys_seen": bool(lora_in_tensors),
        },
        "safetensors_sidecars": {"count": len(sidecars), "files": sidecars[:20]},
    }


def build_report(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    checkpoint, load_info = _load_checkpoint(path, args.allow_cpu_tensor_load, args.no_mmap)
    stat = path.stat()
    report: dict[str, Any] = {
        "schema": "opennmt_py.checkpoint_inventory.v1",
        "path": str(path),
        "file_name": path.name,
        "file_size_bytes": stat.st_size,
        "load": load_info,
        "top_level_type": type(checkpoint).__name__,
    }

    if isinstance(checkpoint, Mapping):
        keys = [str(k) for k in checkpoint.keys()]
        report["top_level_keys"] = keys
        report["top_level_key_count"] = len(keys)
        report["top_level_key_sample"] = keys[: args.max_keys]
        opt = checkpoint.get("opt")
        vocab = checkpoint.get("vocab")
        report["option_summary"] = _option_summary(opt)
        report["vocab_summary"] = _vocab_summary(vocab, args.max_items)
        tensor_sections: dict[str, Any] = {}
        for section in ["model", "generator", "optim"]:
            if section in checkpoint:
                tensor_sections[section] = _tensor_summary(checkpoint[section], args.max_keys)
                tensor_sections[section]["mapping_key_sample"] = _mapping_key_sample(checkpoint[section], args.max_keys)
        report["tensor_sections"] = tensor_sections
        sidecars = _find_sidecars(path)
        report["conversion_readiness"] = _conversion_readiness(checkpoint, report["option_summary"], sidecars)
        missing_gpu_safety = []
        for section, summary in tensor_sections.items():
            devices = set(summary.get("device_counts", {}).keys())
            unsafe = sorted(d for d in devices if d != "cpu" and d != "meta")
            if unsafe:
                missing_gpu_safety.append({"section": section, "devices": unsafe})
        report["gpu_safety"] = {
            "loaded_to_gpu": bool(missing_gpu_safety),
            "non_cpu_devices": missing_gpu_safety,
            "note": "The helper requests CPU/fake tensor loading and never calls CUDA.",
        }
    else:
        report["top_level_keys"] = []
        report["option_summary"] = {"present": False}
        report["vocab_summary"] = {"present": False}
        report["tensor_sections"] = {"root": _tensor_summary(checkpoint, args.max_keys)}
        report["conversion_readiness"] = _conversion_readiness(checkpoint, report["option_summary"], [])

    return report


def print_text_report(report: Mapping[str, Any]) -> None:
    print(f"Checkpoint: {report.get('file_name')} ({report.get('file_size_bytes')} bytes)")
    load = report.get("load", {})
    print(
        "Load mode: {mode}, map_location={map_location}, tensor_data_loaded={loaded}".format(
            mode=load.get("mode"),
            map_location=load.get("map_location"),
            loaded=load.get("tensor_data_loaded"),
        )
    )
    print(f"Top-level type: {report.get('top_level_type')}")
    print("Top-level keys:", ", ".join(report.get("top_level_keys", [])) or "<none>")

    opt = report.get("option_summary", {})
    print("\nOptions:")
    if opt.get("present"):
        print(f"  type={opt.get('type')} field_count={opt.get('field_count')}")
        for key, value in opt.get("selected_fields", {}).items():
            print(f"  {key}: {value}")
    else:
        print("  <missing>")

    vocab = report.get("vocab_summary", {})
    print("\nVocabulary:")
    if vocab.get("present"):
        if "sides" in vocab:
            for side, summary in vocab["sides"].items():
                print(f"  {side}: type={summary.get('type')} length={summary.get('length')} sample={summary.get('sample')}")
        else:
            value = vocab.get("value", {})
            print(f"  type={value.get('type')} length={value.get('length')} sample={value.get('sample')}")
    else:
        print("  <missing>")

    print("\nTensor sections:")
    for section, summary in report.get("tensor_sections", {}).items():
        print(
            f"  {section}: tensors={summary.get('tensor_count')} "
            f"dtypes={summary.get('dtype_counts')} devices={summary.get('device_counts')}"
        )
        sample_names = [item.get("name") for item in summary.get("sample_tensors", [])]
        if sample_names:
            print(f"    samples={sample_names}")

    print("\nReadiness:")
    readiness = report.get("conversion_readiness", {})
    for name, summary in readiness.items():
        print(f"  {name}: {summary}")

    gpu = report.get("gpu_safety", {})
    if gpu:
        print(f"\nGPU safety: loaded_to_gpu={gpu.get('loaded_to_gpu')} ({gpu.get('note')})")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect OpenNMT-py checkpoint metadata, vocab, options, and tensor summaries without loading tensors to GPU."
    )
    parser.add_argument("checkpoint", help="Path to an OpenNMT-py .pt checkpoint metadata file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    parser.add_argument("--max-keys", type=int, default=12, help="Maximum tensor/key samples per section")
    parser.add_argument("--max-items", type=int, default=8, help="Maximum vocab sample items per side")
    parser.add_argument(
        "--allow-cpu-tensor-load",
        action="store_true",
        help="If fake-tensor metadata loading fails, allow full tensor loading on CPU. Use only for trusted checkpoints that fit in RAM.",
    )
    parser.add_argument("--no-mmap", action="store_true", help="Disable torch.load mmap when the installed PyTorch supports it")
    parser.add_argument("--traceback", action="store_true", help="Print Python traceback on failure")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    path = Path(args.checkpoint)
    if not path.is_file():
        print(f"ERROR: checkpoint file does not exist: {path}", file=sys.stderr)
        return 2
    try:
        report = build_report(path, args)
    except Exception as exc:
        if args.traceback:
            traceback.print_exc()
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
