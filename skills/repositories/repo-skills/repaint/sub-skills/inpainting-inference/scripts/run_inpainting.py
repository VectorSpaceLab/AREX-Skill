#!/usr/bin/env python3
"""Safe wrapper for RePaint inpainting inference.

The dry-run path inspects config/layout only. The run path mirrors the upstream inpainting sampler logic.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "README.md").is_file() and (candidate / "test.py").is_file():
            return candidate
    return start


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive runtime guard
        raise SystemExit(
            "PyYAML is required for config inspection. Install the repo runtime deps first."
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise SystemExit(f"{path} did not contain a mapping at the top level")
    return data


def resolve_path(base: Path, raw: str | None) -> Path | None:
    if raw in (None, ""):
        return None
    path = Path(os.path.expanduser(str(raw)))
    if path.is_absolute():
        return path
    return base / path


def list_images_recursive(root: Path) -> list[Path]:
    results: list[Path] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.is_file() and entry.suffix.lower() in IMAGE_EXTS:
            results.append(entry)
        elif entry.is_dir():
            results.extend(list_images_recursive(entry))
    return results


def inspect_rgb(path: Path) -> tuple[tuple[int, int], int, int, bool, list[int], float]:
    try:
        from PIL import Image
        import numpy as np
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive runtime guard
        raise SystemExit(
            "Pillow and numpy are required for dry-run layout inspection. Install the repo runtime deps first."
        ) from exc

    with Image.open(path) as image:
        image = image.convert("RGB")
        array = np.asarray(image)

    height, width = int(array.shape[0]), int(array.shape[1])
    channel0 = array[..., 0]
    channel_equal = bool(
        np.array_equal(array[..., 0], array[..., 1])
        and np.array_equal(array[..., 1], array[..., 2])
    )
    unique_values = [int(v) for v in np.unique(channel0).tolist()]
    mean_value = float(channel0.mean())
    return (width, height), int(channel0.min()), int(channel0.max()), channel_equal, unique_values, mean_value


def inspect_image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive runtime guard
        raise SystemExit(
            "Pillow is required for dry-run layout inspection. Install the repo runtime deps first."
        ) from exc

    with Image.open(path) as image:
        image.load()
        return int(image.size[0]), int(image.size[1])


def print_kv(label: str, value: object) -> None:
    print(f"{label}: {value}")


def inspect_config(conf: dict[str, Any], repo_root: Path, preview_pairs: int) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    data = conf.get("data", {})
    evals = data.get("eval", {}) if isinstance(data, dict) else {}
    if not isinstance(evals, dict) or len(evals) != 1:
        errors.append(
            f"expected exactly one data.eval entry, found {list(evals.keys()) if isinstance(evals, dict) else type(evals).__name__}"
        )
        eval_name = None
        eval_conf: dict[str, Any] = {}
    else:
        eval_name, eval_conf = next(iter(evals.items()))
        if not isinstance(eval_conf, dict):
            errors.append(f"data.eval.{eval_name} must be a mapping")
            eval_conf = {}

    model_path = resolve_path(repo_root, conf.get("model_path"))
    classifier_path = resolve_path(repo_root, conf.get("classifier_path"))
    gt_path = resolve_path(repo_root, eval_conf.get("gt_path"))
    mask_path = resolve_path(repo_root, eval_conf.get("mask_path"))
    paths = eval_conf.get("paths", {}) if isinstance(eval_conf.get("paths", {}), dict) else {}

    print("== RePaint dry-run ==")
    print_kv("config name", conf.get("name"))
    if eval_name is not None:
        print_kv("eval set", eval_name)
    print_kv("repo root", repo_root)
    print_kv("model_path", conf.get("model_path"))
    if model_path is not None:
        print_kv("model exists", model_path.is_file())
    if classifier_path is not None:
        print_kv("classifier_path", conf.get("classifier_path"))
        print_kv("classifier exists", classifier_path.is_file())
    print_kv("image_size", conf.get("image_size"))
    print_kv("class_cond", conf.get("class_cond"))
    print_kv("device", conf.get("device"))
    print_kv("classifier_scale", conf.get("classifier_scale"))
    print_kv("clip_denoised", conf.get("clip_denoised"))
    print_kv("show_progress", conf.get("show_progress"))
    print_kv("batch_size", eval_conf.get("batch_size"))
    print_kv("max_len", eval_conf.get("max_len"))
    print_kv("offset", eval_conf.get("offset"))
    if conf.get("cond_y") is not None:
        print_kv("cond_y", conf.get("cond_y"))
    if conf.get("use_fp16") is not None:
        print_kv("use_fp16", conf.get("use_fp16"))
    if conf.get("use_ddim") is not None:
        print_kv("use_ddim", conf.get("use_ddim"))
        if conf.get("use_ddim"):
            errors.append("use_ddim is true but this checkout does not expose ddim_sample_loop; keep use_ddim false")
    if conf.get("timestep_respacing") not in (None, ""):
        print_kv("timestep_respacing", conf.get("timestep_respacing"))
    if conf.get("schedule_jump_params"):
        print("schedule_jump_params: present (see schedule-visualization for tuning)")

    if conf.get("class_cond") and conf.get("cond_y") is None:
        warnings.append("class_cond is true and cond_y is unset; the runtime will sample random ImageNet labels")
    if not conf.get("class_cond") and conf.get("cond_y") is not None:
        warnings.append("cond_y is set but class_cond is false, so it will be ignored")
    if conf.get("classifier_scale", 0) and conf.get("classifier_path") in (None, ""):
        warnings.append("classifier_scale is positive but classifier_path is absent; classifier guidance will stay off")
    if eval_conf.get("mask_loader") is not True:
        errors.append("data.eval.<name>.mask_loader must be true for inpainting")
    if eval_conf.get("random_crop"):
        errors.append("random_crop is not implemented in this loader; keep it false")
    if eval_conf.get("class_cond"):
        errors.append("data.eval.<name>.class_cond must be false; the loader does not return labels")
    if eval_conf.get("return_dict") is not True:
        errors.append("data.eval.<name>.return_dict must be true; the inpainting loader only implements dict outputs")
    if eval_conf.get("return_dataloader") is not True:
        warnings.append("return_dataloader is false; the example inference path expects a DataLoader")

    required_output_keys = ("srs", "lrs", "gt_keep_masks")
    missing_output_keys = [key for key in required_output_keys if not paths.get(key)]
    if missing_output_keys:
        errors.append(f"missing required output path(s): {', '.join(missing_output_keys)}")
    elif not paths.get("gts"):
        warnings.append("paths.gts is empty or absent; the ground-truth copy will not be written")

    if gt_path is None:
        errors.append("data.eval.<name>.gt_path is missing")
    elif not gt_path.is_dir():
        errors.append(f"gt_path does not exist or is not a directory: {gt_path}")
    if mask_path is None:
        errors.append("data.eval.<name>.mask_path is missing")
    elif not mask_path.is_dir():
        errors.append(f"mask_path does not exist or is not a directory: {mask_path}")
    if model_path is None or not model_path.is_file():
        errors.append(f"model_path does not exist or is not a file: {model_path}")
    if classifier_path is not None and not classifier_path.is_file():
        warnings.append(f"classifier_path does not exist yet: {classifier_path}")

    if gt_path is not None and mask_path is not None and gt_path.is_dir() and mask_path.is_dir():
        gt_files = list_images_recursive(gt_path)
        mask_files = list_images_recursive(mask_path)
        offset = int(eval_conf.get("offset", 0) or 0)
        max_len_value = eval_conf.get("max_len")
        if offset < 0:
            errors.append("offset must be >= 0")
        elif offset > len(gt_files) or offset > len(mask_files):
            errors.append(
                f"offset ({offset}) exceeds available image pairs before slicing ({min(len(gt_files), len(mask_files))})"
            )
        else:
            gt_files = gt_files[offset:]
            mask_files = mask_files[offset:]

        if max_len_value is not None:
            max_len = int(max_len_value)
            if max_len < 1:
                errors.append("max_len must be >= 1 when set")
            elif max_len > len(gt_files) or max_len > len(mask_files):
                errors.append(
                    f"max_len ({max_len}) exceeds available image pairs after offset ({min(len(gt_files), len(mask_files))})"
                )
            else:
                gt_files = gt_files[:max_len]
                mask_files = mask_files[:max_len]

        print_kv("gt files", len(gt_files))
        print_kv("mask files", len(mask_files))
        if len(gt_files) != len(mask_files):
            errors.append("gt_path and mask_path must contain the same number of images; the loader asserts equal lengths")
        preview_count = min(preview_pairs, len(gt_files), len(mask_files))
        if preview_count:
            print(f"previewing {preview_count} pair(s):")
        for idx in range(preview_count):
            gt_file = gt_files[idx]
            mask_file = mask_files[idx]
            gt_w, gt_h = inspect_image_size(gt_file)
            (mask_w, mask_h), mask_min, mask_max, mask_channels_equal, unique_values, mask_mean = inspect_rgb(mask_file)
            print(f"  [{idx + 1}] GT  {gt_file.name}  {gt_w}x{gt_h}")
            print(f"      MSK {mask_file.name}  {mask_w}x{mask_h}  unique={unique_values[:8]}  mean={mask_mean:.2f}")
            if gt_file.name != mask_file.name:
                warnings.append(
                    f"preview pair {idx + 1}: GT basename {gt_file.name!r} differs from mask basename {mask_file.name!r}; pairing follows sorted order, not filename matching"
                )
            if gt_w != mask_w or gt_h != mask_h:
                warnings.append(
                    f"preview pair {idx + 1}: original GT size {gt_w}x{gt_h} differs from mask size {mask_w}x{mask_h}; the loader will center-crop/resize each independently to image_size={conf.get('image_size')}"
                )
            if not mask_channels_equal:
                warnings.append(
                    f"preview pair {idx + 1}: mask channels differ after RGB conversion; keep masks are usually single-channel or replicated RGB"
                )
            if unique_values and any(v not in (0, 255) for v in unique_values):
                warnings.append(
                    f"preview pair {idx + 1}: mask has non-binary values {unique_values[:8]}; the loader scales by 1/255, so non-255 known pixels become soft weights"
                )
            if mask_min == 255 and mask_max == 255:
                warnings.append(
                    f"preview pair {idx + 1}: mask is all-255; the inpainting branch will treat the entire image as known"
                )
            if mask_min == 0 and mask_max == 0:
                warnings.append(
                    f"preview pair {idx + 1}: mask is all-0; the inpainting branch will treat the entire image as unknown"
                )

    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    if errors:
        print("errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("dry-run OK: no blocking config or layout issues detected")
    return 0


def run_sampling(conf_data: dict[str, Any], repo_root: Path) -> int:
    sys.path.insert(0, str(repo_root))

    try:
        import torch as th
        import torch.nn.functional as F
        import conf_mgt
        from guided_diffusion import dist_util
        from guided_diffusion.script_util import (
            NUM_CLASSES,
            classifier_defaults,
            create_classifier,
            create_model_and_diffusion,
            model_and_diffusion_defaults,
            select_args,
        )
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive runtime guard
        raise SystemExit(
            f"Missing runtime dependency while preparing inference: {exc}. Install the repo runtime deps (including blobfile) before running the sampler."
        ) from exc

    def to_u8(sample):
        if sample is None:
            return sample
        sample = ((sample + 1) * 127.5).clamp(0, 255).to(th.uint8)
        sample = sample.permute(0, 2, 3, 1)
        sample = sample.contiguous()
        sample = sample.detach().cpu().numpy()
        return sample

    def main(conf: conf_mgt.Default_Conf):
        print("Start", conf["name"])

        device = dist_util.dev(conf.get("device"))

        model, diffusion = create_model_and_diffusion(
            **select_args(conf, model_and_diffusion_defaults().keys()), conf=conf
        )
        model.load_state_dict(
            dist_util.load_state_dict(os.path.expanduser(conf.model_path), map_location="cpu")
        )
        model.to(device)
        if conf.use_fp16:
            model.convert_to_fp16()
        model.eval()

        show_progress = conf.show_progress

        if conf.classifier_scale > 0 and conf.classifier_path:
            print("loading classifier...")
            classifier = create_classifier(
                **select_args(conf, classifier_defaults().keys())
            )
            classifier.load_state_dict(
                dist_util.load_state_dict(os.path.expanduser(conf.classifier_path), map_location="cpu")
            )
            classifier.to(device)
            if conf.classifier_use_fp16:
                classifier.convert_to_fp16()
            classifier.eval()

            def cond_fn(x, t, y=None, gt=None, **kwargs):
                assert y is not None
                with th.enable_grad():
                    x_in = x.detach().requires_grad_(True)
                    logits = classifier(x_in, t)
                    log_probs = F.log_softmax(logits, dim=-1)
                    selected = log_probs[range(len(logits)), y.view(-1)]
                    return th.autograd.grad(selected.sum(), x_in)[0] * conf.classifier_scale
        else:
            cond_fn = None

        def model_fn(x, t, y=None, gt=None, **kwargs):
            assert y is not None
            return model(x, t, y if conf.class_cond else None, gt=gt)

        print("sampling...")
        dset = "eval"
        eval_name = conf.get_default_eval_name()
        dl = conf.get_dataloader(dset=dset, dsName=eval_name)

        for batch in iter(dl):
            for key in batch.keys():
                if isinstance(batch[key], th.Tensor):
                    batch[key] = batch[key].to(device)

            model_kwargs: dict[str, Any] = {"gt": batch["GT"]}

            gt_keep_mask = batch.get("gt_keep_mask")
            if gt_keep_mask is None:
                raise RuntimeError("Expected gt_keep_mask from the dataset loader; the example inpainting path requires it")
            model_kwargs["gt_keep_mask"] = gt_keep_mask

            batch_size = model_kwargs["gt"].shape[0]
            if conf.cond_y is not None:
                classes = th.ones(batch_size, dtype=th.long, device=device)
                model_kwargs["y"] = classes * conf.cond_y
            else:
                classes = th.randint(low=0, high=NUM_CLASSES, size=(batch_size,), device=device)
                model_kwargs["y"] = classes

            if conf.use_ddim:
                if not hasattr(diffusion, "ddim_sample_loop"):
                    raise RuntimeError("use_ddim is true but ddim_sample_loop is unavailable in this checkout; set use_ddim: false")
                sample_fn = diffusion.ddim_sample_loop
            else:
                sample_fn = diffusion.p_sample_loop
            result = sample_fn(
                model_fn,
                (batch_size, 3, conf.image_size, conf.image_size),
                clip_denoised=conf.clip_denoised,
                model_kwargs=model_kwargs,
                cond_fn=cond_fn,
                device=device,
                progress=show_progress,
                return_all=True,
                conf=conf,
            )
            srs = to_u8(result["sample"])
            gts = to_u8(result["gt"])
            lrs = to_u8(
                result.get("gt") * model_kwargs.get("gt_keep_mask")
                + (-1) * th.ones_like(result.get("gt")) * (1 - model_kwargs.get("gt_keep_mask"))
            )
            gt_keep_masks = to_u8((model_kwargs.get("gt_keep_mask") * 2 - 1))

            conf.eval_imswrite(
                srs=srs,
                gts=gts,
                lrs=lrs,
                gt_keep_masks=gt_keep_masks,
                img_names=batch["GT_name"],
                dset=dset,
                name=eval_name,
                verify_same=False,
            )

        print("sampling complete")
        return 0

    conf_arg = conf_mgt.Default_Conf()
    conf_arg.update(conf_data)
    return main(conf_arg)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe wrapper for RePaint inpainting inference")
    parser.add_argument("--conf_path", required=True, help="Path to a RePaint YAML config")
    parser.add_argument("--dry_run", action="store_true", help="Inspect config/layout only; do not load the checkpoint or sample")
    parser.add_argument("--preview_pairs", type=int, default=3, help="How many GT/mask pairs to print during dry-run inspection")
    parser.add_argument("--device", default=None, help="Optional runtime device override, e.g. cpu, cuda, or cuda:0")
    parser.add_argument("--cond_y", type=int, default=None, help="Optional fixed ImageNet class label for class-conditioned configs")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)

    conf_path = resolve_path(repo_root, args.conf_path)
    if conf_path is None or not conf_path.is_file():
        raise SystemExit(f"Config file not found: {args.conf_path}")

    conf = load_yaml(conf_path)
    if args.device is not None:
        conf["device"] = args.device
    if args.cond_y is not None:
        conf["cond_y"] = args.cond_y

    if args.dry_run:
        return inspect_config(conf, repo_root, max(0, args.preview_pairs))

    return run_sampling(conf, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
