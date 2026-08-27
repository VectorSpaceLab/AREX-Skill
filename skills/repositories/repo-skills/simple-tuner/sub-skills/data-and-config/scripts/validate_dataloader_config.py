#!/usr/bin/env python3
"""Standalone JSON dataloader validator for SimpleTuner.

This script intentionally does not import SimpleTuner. It catches common
structural mistakes before a training launch while avoiding network, model
loading, or cache mutation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable

CORE_DATASET_TYPES = {
    "image",
    "video",
    "audio",
    "text_embeds",
    "image_embeds",
    "conditioning_image_embeds",
    "conditioning",
}
# Additional values present in SimpleTuner source/test surfaces. They are not
# the main user-facing scope of this sub-skill, but accepting them avoids false
# positives for maintainer or generated configs.
EXTRA_RECOGNIZED_DATASET_TYPES = {"eval", "caption", "grounding", "distillation_cache"}
ALL_DATASET_TYPES = CORE_DATASET_TYPES | EXTRA_RECOGNIZED_DATASET_TYPES

BACKEND_TYPES = {"local", "aws", "memory", "csv", "huggingface", "webshart"}
PRIMARY_DATASET_TYPES = {"image", "video", "audio"}
SOURCE_MEDIA_TYPES = {"image", "video", "audio", "conditioning", "eval", "caption", "grounding"}
CACHE_DATASET_TYPES = {"text_embeds", "image_embeds", "conditioning_image_embeds", "distillation_cache"}
CONDITIONING_TYPES = {"controlnet", "mask", "reference_strict", "reference_loose", "grounding"}
INLINE_CONDITIONING_TYPES = {
    "superresolution",
    "sdr",
    "logc3_sdr",
    "jpeg_artifacts",
    "depth",
    "depth_midas",
    "random_masks",
    "inpainting",
    "canny",
    "edges",
    "i2v_first_frame",
    "wan_i2v_first_frame",
}
CAPTION_STRATEGIES = {
    "textfile",
    "instanceprompt",
    "filename",
    "parquet",
    "csv",
    "huggingface",
    "webshart",
    "jsonl",
}
METADATA_BACKENDS = {"discovery", "json", "parquet", "csv", "huggingface", "webshart", "none"}
VALID_CROP_ASPECTS = {"square", "preserve", "random", "closest"}
VALID_CROP_STYLES = {"random", "corner", "center", "centre", "face"}
VALID_AUDIO_TRUNCATION = {"beginning", "end", "random"}


@dataclass(frozen=True)
class Issue:
    severity: str
    location: str
    message: str
    suggestion: str | None = None


class Reporter:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def error(self, location: str, message: str, suggestion: str | None = None) -> None:
        self.issues.append(Issue("ERROR", location, message, suggestion))

    def warning(self, location: str, message: str, suggestion: str | None = None) -> None:
        self.issues.append(Issue("WARNING", location, message, suggestion))

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARNING")

    def print(self) -> None:
        for issue in self.issues:
            print(f"{issue.severity}: {issue.location}: {issue.message}")
            if issue.suggestion:
                print(f"  fix: {issue.suggestion}")
        if not self.issues:
            print("OK: no structural issues found.")
        else:
            status = "FAILED" if self.error_count else "OK_WITH_WARNINGS"
            print(f"{status}: {self.error_count} error(s), {self.warning_count} warning(s).")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a SimpleTuner JSON dataloader for common structural mistakes. "
            "No SimpleTuner import, network access, training, or cache writes are performed."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON dataloader file, or '-' to read JSON from stdin.",
    )
    parser.add_argument(
        "--expect-training-set",
        action="store_true",
        help=(
            "Require an enabled startup-ready primary dataset and text_embeds cache. "
            "Use this for normal training dataloaders, not cache-only fixtures."
        ),
    )
    return parser.parse_args(argv)


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_datasets(payload: Any, reporter: Reporter) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        raw_datasets = payload
    elif isinstance(payload, dict) and isinstance(payload.get("datasets"), list):
        raw_datasets = payload["datasets"]
    else:
        reporter.error(
            "root",
            "Dataloader JSON must be an array of dataset objects or an object with a 'datasets' array.",
            "Use the multidatabackend.json array shape for SimpleTuner training.",
        )
        return []

    datasets: list[dict[str, Any]] = []
    for index, entry in enumerate(raw_datasets):
        if not isinstance(entry, dict):
            reporter.error(f"dataset[{index}]", "Dataset entry must be a JSON object.")
            continue
        datasets.append(entry)
    return datasets


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return False


def is_disabled(dataset: dict[str, Any]) -> bool:
    return as_bool(dataset.get("disabled", dataset.get("disable", False)))


def dataset_type(dataset: dict[str, Any]) -> str:
    value = dataset.get("dataset_type", "image")
    return str(value).strip().lower() if value is not None else "image"


def backend_type(dataset: dict[str, Any]) -> str:
    value = dataset.get("type", "local")
    return str(value).strip().lower() if value is not None else "local"


def dataset_id(dataset: dict[str, Any], index: int) -> str:
    raw = dataset.get("id")
    if raw is None:
        return f"<missing:{index}>"
    return str(raw)


def loc(dataset: dict[str, Any], index: int) -> str:
    raw = dataset.get("id")
    if raw is None or str(raw).strip() == "":
        return f"dataset[{index}]"
    return f"dataset[{index}] id={str(raw)!r}"


def values_as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def require_fields(dataset: dict[str, Any], fields: Iterable[str], location: str, reporter: Reporter) -> None:
    for field in fields:
        if dataset.get(field) in (None, ""):
            reporter.error(location, f"Missing required field {field!r}.")


def normalize_cache_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    # Do not expand user/private paths. Normalize only lexical separators for
    # collision detection and keep unresolved placeholders visible.
    raw = raw.replace("\\", "/")
    try:
        return str(PurePosixPath(os.path.normpath(raw)))
    except Exception:
        return raw


def paths_overlap(left: str, right: str) -> bool:
    left_norm = normalize_cache_path(left)
    right_norm = normalize_cache_path(right)
    if not left_norm or not right_norm:
        return False
    if "{" in left_norm or "{" in right_norm:
        return left_norm == right_norm
    left_parts = PurePosixPath(left_norm).parts
    right_parts = PurePosixPath(right_norm).parts
    if left_parts == right_parts:
        return True
    return left_parts[: len(right_parts)] == right_parts or right_parts[: len(left_parts)] == left_parts


def check_ids(datasets: list[dict[str, Any]], reporter: Reporter) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        raw_id = dataset.get("id")
        if raw_id is None or str(raw_id).strip() == "":
            reporter.error(location, "Dataset id is required and must be non-empty.")
            continue
        key = str(raw_id)
        if key in by_id:
            reporter.error(location, f"Duplicate dataset id {key!r}.", "Each dataset id must be unique and stable.")
        else:
            by_id[key] = dataset
    return by_id


def check_basic_values(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        dtype = dataset_type(dataset)
        btype = backend_type(dataset)

        if dtype not in ALL_DATASET_TYPES:
            reporter.error(
                location,
                f"Unknown dataset_type {dtype!r}.",
                f"Use one of: {', '.join(sorted(CORE_DATASET_TYPES))}.",
            )
        if btype not in BACKEND_TYPES:
            reporter.error(
                location,
                f"Unknown backend type {btype!r}.",
                f"Use one of: {', '.join(sorted(BACKEND_TYPES))}.",
            )

        caption_strategy = dataset.get("caption_strategy")
        if caption_strategy not in (None, ""):
            strategy = str(caption_strategy).strip().lower()
            if strategy not in CAPTION_STRATEGIES:
                reporter.warning(location, f"Unrecognized caption_strategy {strategy!r}.")
        metadata_backend = dataset.get("metadata_backend")
        if metadata_backend not in (None, ""):
            backend = str(metadata_backend).strip().lower()
            if backend not in METADATA_BACKENDS:
                reporter.warning(location, f"Unrecognized metadata_backend {backend!r}.")

        crop_aspect = dataset.get("crop_aspect")
        if crop_aspect not in (None, ""):
            crop_aspect_value = str(crop_aspect).strip().lower()
            if crop_aspect_value not in VALID_CROP_ASPECTS:
                reporter.error(location, f"crop_aspect must be one of {sorted(VALID_CROP_ASPECTS)}, got {crop_aspect!r}.")
            elif crop_aspect_value in {"random", "closest"} and not isinstance(dataset.get("crop_aspect_buckets"), list):
                reporter.error(
                    location,
                    f"crop_aspect={crop_aspect_value!r} requires crop_aspect_buckets as a list.",
                )
        crop_style = dataset.get("crop_style")
        if crop_style not in (None, "") and str(crop_style).strip().lower() not in VALID_CROP_STYLES:
            reporter.error(location, f"crop_style must be one of {sorted(VALID_CROP_STYLES)}, got {crop_style!r}.")


def check_backend_requirements(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        dtype = dataset_type(dataset)
        btype = backend_type(dataset)
        if is_disabled(dataset):
            continue

        if btype == "memory":
            if dtype not in {"text_embeds", "image_embeds"}:
                reporter.error(
                    location,
                    "Memory backend is only valid for text_embeds or image_embeds cache datasets.",
                    "Use local/AWS/CSV/HF/Webshart for primary media or conditioning data.",
                )
            require_fields(dataset, ["cache_dir"], location, reporter)
            mount_path = dataset.get("memory_filesystem_path")
            cache_dir = dataset.get("cache_dir")
            if isinstance(mount_path, str) and isinstance(cache_dir, str) and paths_overlap(mount_path, cache_dir):
                reporter.error(
                    location,
                    "memory_filesystem_path overlaps cache_dir.",
                    "Use an empty mount directory separate from the source cache directory.",
                )
            continue

        if dtype in {"text_embeds", "image_embeds", "conditioning_image_embeds"}:
            if btype not in {"local", "aws", "memory"}:
                reporter.error(location, f"{dtype} caches cannot use backend type {btype!r}.")
            if dtype == "text_embeds" and btype == "local":
                require_fields(dataset, ["cache_dir"], location, reporter)
            if btype == "aws":
                require_fields(dataset, ["aws_bucket_name"], location, reporter)
            continue

        if btype == "local":
            if dtype in SOURCE_MEDIA_TYPES and not dataset.get("auto_generated"):
                require_fields(dataset, ["instance_data_dir"], location, reporter)
        elif btype == "aws":
            require_fields(dataset, ["aws_bucket_name"], location, reporter)
        elif btype == "csv":
            if dtype not in {"image", "video"}:
                reporter.error(location, "CSV backends are for image/video URL manifests, not cache or caption datasets.")
            require_fields(dataset, ["csv_file", "csv_caption_column", "csv_cache_dir"], location, reporter)
        elif btype == "huggingface":
            require_fields(dataset, ["dataset_name"], location, reporter)
            if as_bool(dataset.get("streaming", dataset.get("huggingface", {}).get("streaming") if isinstance(dataset.get("huggingface"), dict) else False)):
                reporter.warning(
                    location,
                    "Hugging Face streaming is not suitable for normal SimpleTuner bucket/length discovery.",
                    "Filter the dataset to a manageable size instead of relying on streaming.",
                )
        elif btype == "webshart":
            webshart_block = dataset.get("webshart") if isinstance(dataset.get("webshart"), dict) else {}
            if not dataset.get("source", webshart_block.get("source")):
                reporter.error(location, "Webshart backend requires a source field.")


def check_caption_metadata(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        dtype = dataset_type(dataset)
        btype = backend_type(dataset)
        caption_strategy = str(dataset.get("caption_strategy", "") or "").strip().lower()
        metadata_backend = str(dataset.get("metadata_backend", "") or "").strip().lower()

        if "caption_filter_list" in dataset and dtype != "text_embeds":
            reporter.error(location, "caption_filter_list is only valid on text_embeds datasets.")

        if caption_strategy == "parquet":
            if metadata_backend != "parquet":
                reporter.error(
                    location,
                    f"caption_strategy='parquet' requires metadata_backend='parquet', got {metadata_backend or '<unset>'!r}.",
                )
            parquet = dataset.get("parquet")
            if not isinstance(parquet, dict):
                reporter.error(location, "caption_strategy='parquet' requires a parquet object.")
            else:
                for field in ("path", "filename_column", "caption_column"):
                    if parquet.get(field) in (None, ""):
                        reporter.error(location, f"parquet.{field} is required for parquet captions.")
                for field in ("width_column", "height_column"):
                    if parquet.get(field) in (None, ""):
                        reporter.warning(location, f"parquet.{field} is recommended to avoid expensive metadata discovery.")

        if caption_strategy == "huggingface" and btype != "huggingface":
            reporter.error(location, "caption_strategy='huggingface' can only be used with type='huggingface'.")
        if btype == "huggingface":
            if metadata_backend and metadata_backend != "huggingface":
                reporter.error(location, "Hugging Face backends require metadata_backend='huggingface'.")
            if caption_strategy and caption_strategy not in {"huggingface", "instanceprompt"}:
                reporter.error(location, "Hugging Face backends require caption_strategy='huggingface' or 'instanceprompt'.")

        if caption_strategy == "webshart" and btype != "webshart":
            reporter.error(location, "caption_strategy='webshart' can only be used with type='webshart'.")
        if btype == "webshart":
            if metadata_backend and metadata_backend != "webshart":
                reporter.error(location, "Webshart backends require metadata_backend='webshart'.")
            if caption_strategy and caption_strategy not in {"webshart", "instanceprompt"}:
                reporter.error(location, "Webshart backends require caption_strategy='webshart' or 'instanceprompt'.")

        if btype == "csv" and caption_strategy and caption_strategy != "csv":
            reporter.warning(location, "CSV backends normally use caption_strategy='csv'.")

        if caption_strategy == "instanceprompt" and not dataset.get("instance_prompt"):
            reporter.warning(location, "caption_strategy='instanceprompt' should provide instance_prompt.")


def check_text_embed_defaults(datasets: list[dict[str, Any]], reporter: Reporter, expect_training_set: bool) -> None:
    enabled_text = [dataset for dataset in datasets if dataset_type(dataset) == "text_embeds" and not is_disabled(dataset)]
    defaults = [dataset for dataset in enabled_text if as_bool(dataset.get("default", False))]
    if len(defaults) > 1:
        ids = ", ".join(str(dataset.get("id", "<missing>")) for dataset in defaults)
        reporter.error("text_embeds", f"Multiple enabled text_embeds datasets are marked default: {ids}.")
    elif len(enabled_text) > 1 and not defaults:
        reporter.error(
            "text_embeds",
            f"{len(enabled_text)} enabled text_embeds datasets are present but none is default.",
            "Set default: true on exactly one text_embeds dataset.",
        )
    elif len(enabled_text) == 1 and not defaults:
        reporter.warning(
            "text_embeds",
            "Single text_embeds dataset has no explicit default: true.",
            "SimpleTuner can choose it, but explicit default avoids ambiguity.",
        )
    elif expect_training_set and not enabled_text:
        reporter.error("text_embeds", "Expected a training set but no enabled text_embeds dataset was found.")


def check_links(datasets: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], reporter: Reporter) -> None:
    referenced_by_conditioning: dict[str, list[str]] = {}
    for index, dataset in enumerate(datasets):
        if dataset_type(dataset) not in {"image", "video"}:
            continue
        current_id = dataset_id(dataset, index)
        for ref in values_as_list(dataset.get("conditioning_data")):
            referenced_by_conditioning.setdefault(str(ref), []).append(current_id)

    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        dtype = dataset_type(dataset)
        current_id = dataset_id(dataset, index)

        def check_reference(field: str, expected_type: str) -> None:
            for ref in values_as_list(dataset.get(field)):
                ref_id = str(ref)
                target = by_id.get(ref_id)
                if target is None:
                    reporter.error(location, f"{field} references missing dataset id {ref_id!r}.")
                    continue
                if dataset_type(target) != expected_type:
                    reporter.error(location, f"{field} references {ref_id!r}, but it is dataset_type={dataset_type(target)!r} not {expected_type!r}.")

        if dtype in {"image", "video"}:
            check_reference("text_embeds", "text_embeds")
            check_reference("image_embeds", "image_embeds")
            check_reference("conditioning_image_embeds", "conditioning_image_embeds")
            for ref in values_as_list(dataset.get("conditioning_data")):
                ref_id = str(ref)
                target = by_id.get(ref_id)
                if target is None:
                    reporter.error(location, f"conditioning_data references missing dataset id {ref_id!r}.")
                    continue
                if dataset_type(target) != "conditioning":
                    reporter.error(location, f"conditioning_data target {ref_id!r} must have dataset_type='conditioning'.")
            for ref in values_as_list(dataset.get("s2v_datasets")):
                ref_id = str(ref)
                target = by_id.get(ref_id)
                if target is None:
                    reporter.error(location, f"s2v_datasets references missing dataset id {ref_id!r}.")
                    continue
                if dataset_type(target) != "audio":
                    reporter.error(location, f"s2v_datasets target {ref_id!r} must have dataset_type='audio'.")

        if dtype == "conditioning":
            conditioning_type = str(dataset.get("conditioning_type", "") or "").strip().lower()
            if conditioning_type and conditioning_type not in CONDITIONING_TYPES:
                reporter.warning(location, f"Unrecognized conditioning_type {conditioning_type!r}.")
            source_id = dataset.get("source_dataset_id")
            if source_id:
                source = by_id.get(str(source_id))
                if source is None:
                    reporter.error(location, f"source_dataset_id references missing dataset id {source_id!r}.")
                elif dataset_type(source) not in {"image", "video"}:
                    reporter.error(location, f"source_dataset_id {source_id!r} should reference an image or video dataset.")
            elif conditioning_type in {"controlnet", "mask", "reference_strict", "grounding"} and current_id not in referenced_by_conditioning:
                reporter.warning(
                    location,
                    "Strict/controlnet/mask conditioning has no source_dataset_id and is not referenced by conditioning_data.",
                    "Set source_dataset_id or link it from the source dataset with conditioning_data.",
                )


def check_inline_conditioning(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        conditioning = dataset.get("conditioning")
        if conditioning in (None, [], {}):
            continue
        location = loc(dataset, index)
        entries = conditioning if isinstance(conditioning, list) else [conditioning]
        if not all(isinstance(entry, dict) for entry in entries):
            reporter.error(location, "conditioning must be an object or an array of objects.")
            continue
        for cond_index, entry in enumerate(entries):
            cond_location = f"{location} conditioning[{cond_index}]"
            cond_type = str(entry.get("type", "") or "").strip().lower()
            if not cond_type:
                reporter.error(cond_location, "Inline conditioning entry requires a type field.")
                continue
            if cond_type not in INLINE_CONDITIONING_TYPES:
                reporter.warning(cond_location, f"Unrecognized inline conditioning type {cond_type!r}.")
            conditioning_type = str(entry.get("conditioning_type", "") or "").strip().lower()
            if conditioning_type and conditioning_type not in CONDITIONING_TYPES:
                reporter.warning(cond_location, f"Unrecognized conditioning_type {conditioning_type!r}.")
            if cond_type in {"canny", "edges"}:
                low = entry.get("low_threshold")
                high = entry.get("high_threshold")
                if low is not None and high is not None:
                    try:
                        low_num = float(low)
                        high_num = float(high)
                    except (TypeError, ValueError):
                        reporter.error(cond_location, "Canny thresholds must be numeric.")
                    else:
                        if low_num < 0 or high_num < 0 or high_num <= low_num:
                            reporter.error(cond_location, "Canny high_threshold must be greater than low_threshold and both non-negative.")


def check_audio_video(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        dtype = dataset_type(dataset)

        audio = dataset.get("audio")
        if isinstance(audio, dict):
            min_duration = audio.get("min_duration_seconds", dataset.get("audio_min_duration_seconds"))
            max_duration = audio.get("max_duration_seconds", dataset.get("audio_max_duration_seconds"))
            if min_duration is not None and max_duration is not None:
                try:
                    if float(max_duration) < float(min_duration):
                        reporter.error(location, "audio.max_duration_seconds must be >= min_duration_seconds.")
                except (TypeError, ValueError):
                    reporter.error(location, "audio min/max duration values must be numeric.")
            interval = audio.get("duration_interval", dataset.get("audio_duration_interval"))
            if interval is not None:
                try:
                    if float(interval) <= 0:
                        reporter.error(location, "audio.duration_interval must be positive.")
                except (TypeError, ValueError):
                    reporter.error(location, "audio.duration_interval must be numeric.")
            truncation = audio.get("truncation_mode", dataset.get("audio_truncation_mode"))
            if truncation and str(truncation).strip().lower() not in VALID_AUDIO_TRUNCATION:
                reporter.error(location, f"audio.truncation_mode must be one of {sorted(VALID_AUDIO_TRUNCATION)}.")
            channels = audio.get("channels", dataset.get("audio_channels"))
            if channels is not None:
                try:
                    if int(channels) < 1:
                        reporter.error(location, "audio.channels must be positive.")
                except (TypeError, ValueError):
                    reporter.error(location, "audio.channels must be an integer.")
            if dtype == "video" and audio.get("auto_split") is False and not dataset.get("s2v_datasets"):
                reporter.warning(location, "audio.auto_split is false and no s2v_datasets are linked.")

        if dtype == "video":
            video = dataset.get("video")
            if isinstance(video, dict):
                num_frames = video.get("num_frames")
                min_frames = video.get("min_frames")
                for field_name, value in (("num_frames", num_frames), ("min_frames", min_frames), ("max_frames", video.get("max_frames"))):
                    if value is None:
                        continue
                    try:
                        if int(value) < 1:
                            reporter.error(location, f"video.{field_name} must be positive.")
                    except (TypeError, ValueError):
                        reporter.error(location, f"video.{field_name} must be an integer.")
                if num_frames is not None and min_frames is not None:
                    try:
                        if int(min_frames) < int(num_frames):
                            reporter.error(location, "video.min_frames must be >= video.num_frames.")
                    except (TypeError, ValueError):
                        pass
                if video.get("bucket_strategy") == "resolution_frames" and num_frames is not None:
                    reporter.warning(location, "resolution_frames with fixed num_frames may collapse to one frame bucket.")


def check_grounding(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        grounding = dataset.get("grounding")
        if not isinstance(grounding, dict) or not as_bool(grounding.get("enabled", False)):
            continue
        location = loc(dataset, index)
        if dataset_type(dataset) not in {"image", "video"}:
            reporter.error(location, "grounding.enabled only applies to image or video source datasets.")
        auto_detect = grounding.get("auto_detect")
        if isinstance(auto_detect, dict) and as_bool(auto_detect.get("enabled", False)) and backend_type(dataset) != "local":
            reporter.error(location, "grounding.auto_detect requires a local backend.")
        reporter.warning(
            location,
            "grounding.enabled also requires training config max_grounding_entities > 0 to have effect.",
        )


def check_size_and_schedule(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    for index, dataset in enumerate(datasets):
        location = loc(dataset, index)
        maximum_image_size = dataset.get("maximum_image_size")
        target_downsample_size = dataset.get("target_downsample_size")
        resolution_type = str(dataset.get("resolution_type", "") or "").strip().lower()
        if maximum_image_size not in (None, "") and target_downsample_size in (None, ""):
            reporter.error(location, "maximum_image_size requires target_downsample_size.")
        if resolution_type and resolution_type not in {"pixel", "pixel_area", "area"}:
            reporter.error(location, "resolution_type must be 'pixel', 'pixel_area', or 'area'.")

        def number(field: str) -> float | None:
            value = dataset.get(field)
            if value in (None, ""):
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                reporter.error(location, f"{field} must be numeric.")
                return None

        start_epoch = number("start_epoch")
        end_epoch = number("end_epoch")
        start_step = number("start_step")
        end_step = number("end_step")
        for field in ("start_epoch", "start_step", "end_epoch", "end_step"):
            value = number(field)
            if value is not None and value < 0:
                reporter.error(location, f"{field} must be non-negative.")
        if start_epoch is not None and end_epoch is not None and end_epoch < start_epoch:
            reporter.error(location, "end_epoch must be >= start_epoch.")
        if start_step is not None and end_step is not None and end_step < start_step:
            reporter.error(location, "end_step must be >= start_step.")


def check_cache_collisions(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    seen: dict[tuple[str, str], str] = {}
    role_paths: dict[str, list[tuple[str, str]]] = {}
    for index, dataset in enumerate(datasets):
        if is_disabled(dataset):
            continue
        did = dataset_id(dataset, index)
        candidates = {
            "text_cache": dataset.get("cache_dir") if dataset_type(dataset) == "text_embeds" else None,
            "embed_cache": dataset.get("cache_dir") if dataset_type(dataset) in {"image_embeds", "conditioning_image_embeds"} else None,
            "vae_cache": dataset.get("cache_dir_vae"),
            "conditioning_image_embed_cache": dataset.get("cache_dir_conditioning_image_embeds"),
        }
        for role, value in candidates.items():
            normalized = normalize_cache_path(value)
            if not normalized:
                continue
            key = (role, normalized)
            if key in seen:
                reporter.warning(
                    "cache",
                    f"{role} path {normalized!r} is shared by {seen[key]!r} and {did!r}.",
                    "Use distinct cache directories unless sharing is intentional.",
                )
            else:
                seen[key] = did
            role_paths.setdefault(normalized, []).append((role, did))
    for normalized, uses in role_paths.items():
        roles = {role for role, _did in uses}
        ids = {did for _role, did in uses}
        if len(roles) > 1 and len(ids) > 1:
            reporter.warning(
                "cache",
                f"Path {normalized!r} is used for multiple cache roles: {', '.join(sorted(roles))}.",
                "Separate text, VAE, image, and conditioning image embed caches.",
            )


def check_expect_training_set(datasets: list[dict[str, Any]], reporter: Reporter) -> None:
    enabled_primary = [dataset for dataset in datasets if dataset_type(dataset) in PRIMARY_DATASET_TYPES and not is_disabled(dataset)]
    if not enabled_primary:
        reporter.error("training-set", "Expected a training set but no enabled primary image/video/audio dataset was found.")
        return

    startup_ready = []
    for dataset in enabled_primary:
        start_epoch = dataset.get("start_epoch", 1)
        start_step = dataset.get("start_step", 0)
        try:
            is_ready = float(start_epoch) <= 1 and float(start_step) <= 1
        except (TypeError, ValueError):
            is_ready = False
        if is_ready:
            startup_ready.append(dataset)
    if not startup_ready:
        reporter.error(
            "training-set",
            "All enabled primary datasets are scheduled for later; at least one must be available at startup.",
        )


def validate(payload: Any, expect_training_set: bool) -> Reporter:
    reporter = Reporter()
    datasets = extract_datasets(payload, reporter)
    if not datasets:
        return reporter
    by_id = check_ids(datasets, reporter)
    check_basic_values(datasets, reporter)
    check_backend_requirements(datasets, reporter)
    check_caption_metadata(datasets, reporter)
    check_text_embed_defaults(datasets, reporter, expect_training_set)
    check_links(datasets, by_id, reporter)
    check_inline_conditioning(datasets, reporter)
    check_audio_video(datasets, reporter)
    check_grounding(datasets, reporter)
    check_size_and_schedule(datasets, reporter)
    check_cache_collisions(datasets, reporter)
    if expect_training_set:
        check_expect_training_set(datasets, reporter)
    return reporter


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = load_json(args.input)
    except FileNotFoundError:
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {args.input}: {exc}", file=sys.stderr)
        return 2
    reporter = validate(payload, args.expect_training_set)
    reporter.print()
    return 1 if reporter.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
