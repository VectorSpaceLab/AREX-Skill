#!/usr/bin/env python3
"""Safely resample a directory of audio files for Coqui TTS workflows."""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resample audio recursively. Writes to a separate output directory by default; in-place mutation requires --in-place."
    )
    parser.add_argument("--input-dir", required=True, help="Directory containing audio files.")
    parser.add_argument("--output-sr", required=True, type=int, help="Target sample rate, e.g. 22050.")
    parser.add_argument("--output-dir", help="Destination directory. Required unless --in-place is set.")
    parser.add_argument("--in-place", action="store_true", help="Rewrite matching files under --input-dir. Requires --overwrite.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--file-ext", default="wav", help="Audio extension to resample. Default: wav")
    parser.add_argument("--n-jobs", type=int, default=1, help="Parallel worker count. Default: 1")
    parser.add_argument("--no-verify", action="store_true", help="Skip output sample-rate verification.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned file operations without reading or writing audio.")
    return parser.parse_args()


def collect_files(input_dir: Path, file_ext: str) -> List[Path]:
    ext = file_ext.lower().lstrip(".")
    return sorted(p for p in input_dir.rglob(f"*.{ext}") if p.is_file())


def build_tasks(files: Iterable[Path], input_dir: Path, output_dir: Path | None, in_place: bool) -> List[Tuple[str, str]]:
    tasks = []
    for src in files:
        if in_place:
            dst = src
        else:
            assert output_dir is not None
            dst = output_dir / src.relative_to(input_dir)
        tasks.append((str(src), str(dst)))
    return tasks


def resample_one(task: Tuple[str, str, int, bool, bool]) -> Dict[str, object]:
    src_raw, dst_raw, output_sr, overwrite, verify = task
    src = Path(src_raw)
    dst = Path(dst_raw)
    if dst.exists() and not overwrite and src != dst:
        return {"src": src_raw, "dst": dst_raw, "status": "skipped", "reason": "output exists"}
    if src == dst and not overwrite:
        return {"src": src_raw, "dst": dst_raw, "status": "skipped", "reason": "in-place requires --overwrite"}

    import librosa
    import soundfile as sf

    try:
        # Coqui's utility uses librosa.load(..., sr=target), which produces mono
        # audio by default. Preserve that TTS-oriented behavior here.
        y, sr = librosa.load(str(src), sr=output_sr, mono=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(dst), y, sr)
        if verify:
            info = sf.info(str(dst))
            if int(info.samplerate) != int(output_sr):
                return {
                    "src": src_raw,
                    "dst": dst_raw,
                    "status": "error",
                    "reason": f"verified sample rate {info.samplerate} != {output_sr}",
                }
        return {"src": src_raw, "dst": dst_raw, "status": "ok", "sample_rate": output_sr}
    except Exception as exc:  # pragma: no cover - environment/audio dependent
        return {"src": src_raw, "dst": dst_raw, "status": "error", "reason": repr(exc)}


def validate_args(args: argparse.Namespace) -> Tuple[Path, Path | None, int]:
    input_dir = Path(args.input_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else None
    if not input_dir.is_dir():
        raise ValueError(f"--input-dir is not a directory: {input_dir}")
    if args.output_sr <= 0:
        raise ValueError("--output-sr must be positive")
    if args.n_jobs <= 0:
        raise ValueError("--n-jobs must be positive")
    if args.in_place:
        if output_dir is not None:
            raise ValueError("use either --in-place or --output-dir, not both")
        if not args.overwrite and not args.dry_run:
            raise ValueError("--in-place requires --overwrite so mutation is explicit")
    else:
        if output_dir is None:
            raise ValueError("--output-dir is required unless --in-place is set")
        try:
            if output_dir.resolve() == input_dir.resolve():
                raise ValueError("--output-dir must not be the same as --input-dir")
        except FileNotFoundError:
            # Parent may not exist yet; compare absolute strings as a fallback.
            if output_dir.absolute() == input_dir.absolute():
                raise ValueError("--output-dir must not be the same as --input-dir")
    return input_dir, output_dir, args.n_jobs


def main() -> int:
    args = parse_args()
    try:
        input_dir, output_dir, n_jobs = validate_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    files = collect_files(input_dir, args.file_ext)
    if not files:
        print(f"error: no .{args.file_ext.lstrip('.')} files found in {input_dir}", file=sys.stderr)
        return 2

    pairs = build_tasks(files, input_dir, output_dir, args.in_place)
    print(f"files selected: {len(pairs)}")
    print(f"target sample rate: {args.output_sr}")
    print(f"mode: {'in-place' if args.in_place else 'copy-to-output-dir'}")
    if args.dry_run:
        for src, dst in pairs[:20]:
            print(f"  {src} -> {dst}")
        if len(pairs) > 20:
            print(f"  ... {len(pairs) - 20} more")
        return 0

    worker_tasks = [(src, dst, args.output_sr, args.overwrite, not args.no_verify) for src, dst in pairs]
    results: List[Dict[str, object]] = []
    if n_jobs == 1:
        for task in worker_tasks:
            results.append(resample_one(task))
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as executor:
            for result in executor.map(resample_one, worker_tasks):
                results.append(result)

    counts: Dict[str, int] = {}
    for result in results:
        counts[str(result["status"])] = counts.get(str(result["status"]), 0) + 1
    print("summary:")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")

    errors = [r for r in results if r["status"] == "error"]
    skipped = [r for r in results if r["status"] == "skipped"]
    if skipped:
        print("skipped examples:")
        for item in skipped[:10]:
            print(f"  - {item['src']} -> {item['dst']}: {item.get('reason')}")
    if errors:
        print("errors:", file=sys.stderr)
        for item in errors[:20]:
            print(f"  - {item['src']} -> {item['dst']}: {item.get('reason')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
