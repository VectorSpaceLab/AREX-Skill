#!/usr/bin/env python3
"""Safe Sana dataset layout validator.

This script performs small, local metadata checks only. It never launches
training, loads model checkpoints, imports torch, or downloads datasets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tarfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTS = {".mp4", ".npy"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    def print(self) -> None:
        for message in self.info:
            print(f"INFO: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}")
        for message in self.errors:
            print(f"ERROR: {message}")
        if self.errors:
            print(f"RESULT: invalid ({len(self.errors)} error(s), {len(self.warnings)} warning(s))")
        else:
            print(f"RESULT: ok ({len(self.warnings)} warning(s))")


def load_json(path: Path, report: Report) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validator should keep going
        report.error(f"Cannot parse JSON {path}: {exc}")
        return None


def safe_rel(value: str) -> bool:
    p = Path(str(value))
    return not p.is_absolute() and ".." not in p.parts


def iter_limited(items: Iterable[Any], limit: int) -> Iterable[Any]:
    for index, item in enumerate(items):
        if index >= limit:
            break
        yield item


def validate_image_pair(path: Path, args: argparse.Namespace, report: Report) -> None:
    if not path.is_dir():
        report.error(f"Image-pair path is not a directory: {path}")
        return

    images = sorted([p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXTS])
    txts = {p.stem for p in path.iterdir() if p.suffix.lower() == ".txt"}
    report.note(f"Found {len(images)} image file(s) and {len(txts)} text caption file(s).")
    if not images:
        report.error("No image files with extensions .png/.jpg/.jpeg/.webp found.")

    for img in iter_limited(images, args.max_samples):
        if img.stem not in txts:
            report.error(f"Missing caption text for image {img.name}: expected {img.stem}.txt")
        else:
            txt_path = path / f"{img.stem}.txt"
            try:
                first_line = txt_path.read_text(encoding="utf-8").splitlines()[0].strip()
            except IndexError:
                first_line = ""
            except Exception as exc:  # noqa: BLE001
                report.error(f"Cannot read caption {txt_path.name}: {exc}")
                continue
            if not first_line:
                report.warn(f"Caption file is empty or first line blank: {txt_path.name}")

    meta_path = path / "meta_data.json"
    if meta_path.exists():
        meta = load_json(meta_path, report)
        if isinstance(meta, dict):
            names = meta.get("img_names")
            if not isinstance(names, list):
                report.error("meta_data.json exists but does not contain list field img_names.")
            else:
                report.note(f"meta_data.json lists {len(names)} image name entry/entries.")
                available_stems = {p.stem for p in images}
                available_names = {p.name for p in images} | available_stems
                missing = [str(name) for name in names[: args.max_samples] if str(name) not in available_names]
                if missing:
                    report.warn(
                        "Some meta_data.json img_names do not match observed image basenames or filenames: "
                        + ", ".join(missing[:10])
                    )
    elif args.require_meta:
        report.error("meta_data.json is required for SanaImgDataset but was not found.")
    else:
        report.warn("meta_data.json not found. SanaImgDataset expects it; create it before training.")


def tar_member_groups(tar_path: Path, max_members: int, report: Report) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    try:
        with tarfile.open(tar_path, "r") as tar:
            for member in iter_limited(tar, max_members):
                if not member.isfile():
                    continue
                name = Path(member.name)
                groups.setdefault(str(name.with_suffix("")), set()).add(name.suffix.lower())
    except Exception as exc:  # noqa: BLE001
        report.error(f"Cannot read tar shard {tar_path.name}: {exc}")
    return groups


def validate_wids(path: Path, args: argparse.Namespace, report: Report) -> None:
    if not path.is_dir():
        report.error(f"WIDS path is not a directory: {path}")
        return
    tar_files = sorted(path.glob("*.tar"))
    report.note(f"Found {len(tar_files)} tar shard(s).")
    if not tar_files:
        report.error("No .tar shards found for SanaWebDatasetMS.")

    meta_path = path / "wids-meta.json"
    if not meta_path.exists():
        report.error("wids-meta.json not found. Generate it with tools/create_wids_metadata.py.")
    else:
        meta = load_json(meta_path, report)
        if isinstance(meta, dict):
            shardlist = meta.get("shardlist")
            if not isinstance(shardlist, list):
                report.error("wids-meta.json does not contain a shardlist list.")
            else:
                report.note(f"wids-meta.json lists {len(shardlist)} shard(s).")
                existing = {p.name for p in tar_files}
                for item in shardlist[: args.max_samples]:
                    url = item.get("url") if isinstance(item, dict) else None
                    if not url:
                        report.error("A wids-meta shard entry is missing url.")
                    elif Path(str(url)).name not in existing:
                        report.error(f"wids-meta shard url not found next to metadata: {url}")
                    nsamples = item.get("nsamples") if isinstance(item, dict) else None
                    if nsamples is not None and int(nsamples) <= 0:
                        report.warn(f"Shard {url} reports nsamples={nsamples}.")

    for tar_path in tar_files[: args.max_samples]:
        groups = tar_member_groups(tar_path, args.max_tar_members, report)
        if not groups:
            report.warn(f"Tar shard has no inspected sample-like members: {tar_path.name}")
            continue
        complete = 0
        latent = 0
        missing_json: list[str] = []
        for stem, exts in groups.items():
            has_media = bool(exts & IMAGE_EXTS) or ".npy" in exts
            if has_media and ".json" not in exts:
                missing_json.append(stem)
            if has_media and ".json" in exts:
                complete += 1
            if ".npy" in exts:
                latent += 1
        report.note(f"{tar_path.name}: inspected {len(groups)} basename group(s), {complete} media+json pair(s).")
        if latent:
            report.note(f"{tar_path.name}: observed {latent} .npy latent-like member group(s).")
        if missing_json:
            report.warn(f"{tar_path.name}: media member(s) without same-basename .json: {missing_json[:5]}")


def zip_member_names(zip_path: Path, report: Report) -> list[str]:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            return zf.namelist()
    except Exception as exc:  # noqa: BLE001
        report.error(f"Cannot read zip {zip_path.name}: {exc}")
        return []


def validate_sana_zip_video(path: Path, args: argparse.Namespace, report: Report) -> None:
    if not path.is_dir():
        report.error(f"Video zip path is not a directory: {path}")
        return
    zips = sorted(path.glob("*.zip"))
    report.note(f"Found {len(zips)} zip shard(s).")
    if not zips:
        report.error("No .zip shards found for SanaZipDataset.")
        return
    for zip_path in zips[: args.max_samples]:
        names = zip_member_names(zip_path, report)
        stems: dict[str, set[str]] = {}
        for name in names:
            p = Path(name)
            if p.suffix.lower() in VIDEO_EXTS or p.suffix.lower() == ".json":
                stems.setdefault(str(p.with_suffix("")), set()).add(p.suffix.lower())
        media = [stem for stem, exts in stems.items() if exts & VIDEO_EXTS]
        missing_json = [stem for stem in media if ".json" not in stems.get(stem, set())]
        report.note(f"{zip_path.name}: found {len(media)} media member(s) with {len(media)-len(missing_json)} json pair(s).")
        if missing_json:
            report.warn(f"{zip_path.name}: media member(s) without same-basename .json: {missing_json[:5]}")
        for name in names[: args.max_zip_members]:
            if name.endswith(".json"):
                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        data = json.loads(zf.read(name).decode("utf-8"))
                    for key in ("prompt", "width", "height"):
                        if key not in data:
                            report.warn(f"{zip_path.name}:{name} missing recommended key {key!r}.")
                except Exception as exc:  # noqa: BLE001
                    report.warn(f"Cannot parse {zip_path.name}:{name}: {exc}")
                break


def validate_streaming_v2v(path: Path, args: argparse.Namespace, report: Report) -> None:
    manifest = path / "manifest.jsonl"
    if not manifest.is_file():
        report.error(f"Streaming V2V manifest not found: {manifest}")
        return
    required = {"id", "shard", "source_member", "target_member", "prompt", "width", "height"}
    seen: set[str] = set()
    rows = 0
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if rows >= args.max_samples:
            break
        rows += 1
        try:
            row = json.loads(line)
        except Exception as exc:  # noqa: BLE001
            report.error(f"manifest.jsonl:{line_no} invalid JSON: {exc}")
            continue
        missing = sorted(required - row.keys())
        if missing:
            report.error(f"manifest.jsonl:{line_no} missing fields: {missing}")
        sample_id = str(row.get("id", ""))
        if sample_id in seen:
            report.error(f"manifest.jsonl:{line_no} duplicate id {sample_id!r}")
        seen.add(sample_id)
        for field in ("shard", "source_member", "target_member"):
            value = str(row.get(field, ""))
            if not safe_rel(value):
                report.error(f"manifest.jsonl:{line_no} {field} must be dataset-relative and not contain '..': {value}")
        shard = path / str(row.get("shard", ""))
        if row.get("shard") and not shard.is_file():
            report.error(f"manifest.jsonl:{line_no} shard does not exist: {shard}")
        elif shard.is_file():
            names = set(zip_member_names(shard, report))
            for field in ("source_member", "target_member"):
                member = str(row.get(field, ""))
                if member and member not in names:
                    report.error(f"manifest.jsonl:{line_no} {field} not found in shard {shard.name}: {member}")
    report.note(f"Inspected {rows} manifest row(s) from {manifest.name}.")
    checksum = path / "checksums.sha256"
    if checksum.exists():
        report.note("checksums.sha256 found; run `sha256sum -c checksums.sha256` before training.")


def validate_long_v2v(path: Path, args: argparse.Namespace, report: Report) -> None:
    manifest = path / "manifest.jsonl"
    if not manifest.is_file():
        report.error(f"Long V2V manifest not found: {manifest}")
        return
    required = {"prompt", "reverse_prompt", "source_video"}
    rows = 0
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if rows >= args.max_samples:
            break
        rows += 1
        try:
            row = json.loads(line)
        except Exception as exc:  # noqa: BLE001
            report.error(f"manifest.jsonl:{line_no} invalid JSON: {exc}")
            continue
        missing = sorted(required - row.keys())
        if missing:
            report.error(f"manifest.jsonl:{line_no} missing fields: {missing}")
        source = str(row.get("source_video", ""))
        if source and not safe_rel(source):
            report.error(f"manifest.jsonl:{line_no} source_video must stay inside data root: {source}")
        elif source and not (path / source).is_file():
            report.warn(f"manifest.jsonl:{line_no} source_video not found locally: {source}")
        for field in ("prompt", "reverse_prompt"):
            if not str(row.get(field, "")).strip():
                report.warn(f"manifest.jsonl:{line_no} {field} is blank.")
    report.note(f"Inspected {rows} long V2V manifest row(s).")


def validate_wm_zip_latent(path: Path, args: argparse.Namespace, report: Report) -> None:
    cache = Path(args.vae_cache_dir).expanduser() if args.vae_cache_dir else None
    if not path.is_dir():
        report.error(f"WM raw data path is not a directory: {path}")
        return
    if cache is None:
        report.error("--vae-cache-dir is required for wm-zip-latent validation.")
        return
    if not cache.is_dir():
        report.error(f"WM VAE cache path is not a directory: {cache}")
        return
    raw_zips = sorted(path.glob("*.zip"))
    report.note(f"Found {len(raw_zips)} raw zip(s) and {len(list(cache.glob('*.zip')))} cache zip(s).")
    if not raw_zips:
        report.error("No raw .zip files found.")
        return
    for raw_zip in raw_zips[: args.max_samples]:
        cache_zip = cache / raw_zip.name
        if not cache_zip.is_file():
            report.error(f"Missing matching latent cache zip for {raw_zip.name}: {cache_zip}")
            continue
        raw_names = zip_member_names(raw_zip, report)
        cache_names = zip_member_names(cache_zip, report)
        raw_keys = {Path(n).with_suffix("").as_posix() for n in raw_names if n.endswith(".json")}
        cache_keys = {Path(n).with_suffix("").as_posix() for n in cache_names if n.endswith(".npz")}
        matches = sorted(raw_keys & cache_keys)
        report.note(f"{raw_zip.name}: {len(matches)} json/latent key match(es) inspected by name.")
        if not matches:
            report.warn(f"{raw_zip.name}: no same-key raw JSON and latent NPZ entries found.")
        camera = raw_zip.with_name(raw_zip.stem + "_camera.npz")
        if camera.exists():
            report.note(f"{raw_zip.name}: camera sidecar found: {camera.name}")
        else:
            report.warn(f"{raw_zip.name}: camera sidecar not found; loader will fall back to identity cameras.")
        for suffix in ("_vmafmotion.json", "_unimatch.json", "_dover.json", "_vlm_entity_filter.json", "_vlm_quality_filter.json"):
            sidecar = raw_zip.with_name(raw_zip.stem + suffix)
            if sidecar.exists():
                report.note(f"{raw_zip.name}: filter sidecar found: {sidecar.name}")
    report.warn("SANA-WM public Sekai-derived data is non-commercial research use only; verify dataset license before training.")


def validate_lora(path: Path, args: argparse.Namespace, report: Report) -> None:
    if not path.is_dir():
        report.error(f"LoRA instance path is not a directory: {path}")
        return
    images = sorted([p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS])
    report.note(f"Found {len(images)} instance image(s) for DreamBooth LoRA.")
    if not images:
        report.error("No instance images found for LoRA training.")
    if len(images) < 3:
        report.warn("DreamBooth examples typically use at least 3-5 subject images.")
    if len(images) > 200:
        report.warn("Large instance set detected; LoRA hyperparameters may need adjustment.")
    txts = [p for p in path.rglob("*.txt")]
    if txts:
        report.note("Caption text files exist, but DreamBooth LoRA primarily uses --instance_prompt.")


def detect_mode(path: Path) -> str:
    if (path / "manifest.jsonl").is_file():
        # Distinguish by peeking at the first JSONL row.
        try:
            for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    if {"id", "shard", "source_member", "target_member"}.issubset(row):
                        return "streaming-v2v"
                    if {"prompt", "reverse_prompt", "source_video"}.issubset(row):
                        return "long-v2v"
                    break
        except Exception:
            return "long-v2v"
    if (path / "wids-meta.json").is_file() or list(path.glob("*.tar")):
        return "wids"
    if list(path.glob("*.zip")):
        return "sana-zip-video"
    if (path / "meta_data.json").is_file() or any(p.suffix.lower() in IMAGE_EXTS for p in path.iterdir() if p.is_file()):
        return "image-pair"
    return "image-pair"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, help="Dataset root or manifest directory to validate.")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=[
            "auto",
            "image-pair",
            "wids",
            "sana-zip-video",
            "streaming-v2v",
            "long-v2v",
            "wm-zip-latent",
            "lora",
        ],
        help="Dataset layout mode. auto infers from local files.",
    )
    parser.add_argument("--vae-cache-dir", default=None, help="Matching VAE latent cache directory for wm-zip-latent.")
    parser.add_argument("--max-samples", type=int, default=20, help="Maximum files/rows/shards to inspect.")
    parser.add_argument("--max-tar-members", type=int, default=200, help="Maximum members to inspect per tar shard.")
    parser.add_argument("--max-zip-members", type=int, default=200, help="Maximum members to inspect per zip shard.")
    parser.add_argument("--require-meta", action="store_true", help="Treat missing image-pair meta_data.json as an error.")
    args = parser.parse_args(argv)

    path = Path(args.path).expanduser()
    report = Report()
    if not path.exists():
        report.error(f"Path does not exist: {path}")
        report.print()
        return 1

    mode = detect_mode(path) if args.mode == "auto" else args.mode
    report.note(f"Validation mode: {mode}")

    validators = {
        "image-pair": validate_image_pair,
        "wids": validate_wids,
        "sana-zip-video": validate_sana_zip_video,
        "streaming-v2v": validate_streaming_v2v,
        "long-v2v": validate_long_v2v,
        "wm-zip-latent": validate_wm_zip_latent,
        "lora": validate_lora,
    }
    validators[mode](path, args, report)

    report.print()
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
