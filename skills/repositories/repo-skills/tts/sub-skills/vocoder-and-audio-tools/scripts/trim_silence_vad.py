#!/usr/bin/env python3
"""Trim silence with Silero/Coqui VAD using explicit cache/network acknowledgement.

`--help` and `--dry-run` do not import torch or download models. A real run
loads a Silero VAD model through torch.hub or from a user-provided local source.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trim leading/trailing silence or all non-speech with Silero VAD. Requires explicit model cache/network acknowledgement for real runs."
    )
    parser.add_argument("-i", "--input-dir", required=True, help="Input audio directory.")
    parser.add_argument("-o", "--output-dir", help="Output directory. Required unless --in-place is set.")
    parser.add_argument("-g", "--glob", default="**/*.wav", help="Glob pattern relative to input dir. Default: **/*.wav")
    parser.add_argument("--in-place", action="store_true", help="Rewrite matching files under input dir. Requires --force.")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing outputs or allow in-place rewriting.")
    parser.add_argument(
        "--trim-all-nonspeech",
        action="store_true",
        help="Remove all non-speech chunks, not just leading/trailing non-speech. More destructive.",
    )
    parser.add_argument("--use-cuda", action="store_true", help="Move VAD model/audio tensors to CUDA.")
    parser.add_argument("--use-onnx", action="store_true", help="Request ONNX mode from Silero VAD torch.hub loader.")
    parser.add_argument(
        "--hub-repo",
        default="snakers4/silero-vad",
        help="Torch Hub repo or local Silero VAD source directory. Default: snakers4/silero-vad",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Acknowledge that torch.hub may use network/cache to load the default Silero VAD model.",
    )
    parser.add_argument("--force-reload", action="store_true", help="Force torch.hub to refresh the model cache.")
    parser.add_argument("--dry-run", action="store_true", help="List planned files and exit without importing torch or loading VAD.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> Tuple[Path, Path, bool]:
    input_dir = Path(args.input_dir).expanduser()
    if not input_dir.is_dir():
        raise ValueError(f"--input-dir is not a directory: {input_dir}")
    if args.in_place:
        if args.output_dir:
            raise ValueError("use either --in-place or --output-dir, not both")
        if not args.force and not args.dry_run:
            raise ValueError("--in-place requires --force so mutation is explicit")
        output_dir = input_dir
    else:
        if not args.output_dir:
            raise ValueError("--output-dir is required unless --in-place is set")
        output_dir = Path(args.output_dir).expanduser()
        try:
            if output_dir.resolve() == input_dir.resolve():
                raise ValueError("--output-dir must not be the same as --input-dir; use --in-place explicitly")
        except FileNotFoundError:
            if output_dir.absolute() == input_dir.absolute():
                raise ValueError("--output-dir must not be the same as --input-dir; use --in-place explicitly")
    hub_repo = Path(args.hub_repo).expanduser()
    repo_is_local = hub_repo.exists()
    if repo_is_local:
        args.hub_repo = str(hub_repo)
    if not args.dry_run and not repo_is_local and not args.allow_download:
        raise ValueError(
            "default torch.hub loading may require network/cache access; pass --allow-download after approval or use --hub-repo /path/to/local/silero-vad"
        )
    return input_dir, output_dir, repo_is_local


def collect_files(input_dir: Path, pattern: str) -> List[Path]:
    return sorted(p for p in input_dir.glob(pattern) if p.is_file())


def output_for(src: Path, input_dir: Path, output_dir: Path) -> Path:
    return output_dir / src.relative_to(input_dir)


def load_vad_model(args: argparse.Namespace, repo_is_local: bool):
    import torch

    source = "local" if repo_is_local else "github"
    model, utils = torch.hub.load(
        repo_or_dir=args.hub_repo,
        model="silero_vad",
        source=source,
        force_reload=args.force_reload,
        onnx=args.use_onnx,
        force_onnx_cpu=True,
    )
    if args.use_cuda:
        model = model.cuda()
    get_speech_timestamps, save_audio, _, _, collect_chunks = utils
    return model, get_speech_timestamps, save_audio, collect_chunks


def trim_one(model_and_utils, src: Path, dst: Path, force: bool, trim_edges_only: bool, use_cuda: bool) -> Dict[str, object]:
    if dst.exists() and not force and src != dst:
        return {"src": str(src), "dst": str(dst), "status": "skipped", "reason": "output exists"}
    if src == dst and not force:
        return {"src": str(src), "dst": str(dst), "status": "skipped", "reason": "in-place requires --force"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        from TTS.utils.vad import remove_silence

        out_path, is_speech = remove_silence(
            model_and_utils,
            str(src),
            str(dst),
            trim_just_beginning_and_end=trim_edges_only,
            use_cuda=use_cuda,
        )
        if out_path is None:
            return {"src": str(src), "dst": str(dst), "status": "filtered", "speech": False}
        return {"src": str(src), "dst": str(dst), "status": "ok" if is_speech else "filtered", "speech": bool(is_speech)}
    except Exception as exc:  # pragma: no cover - environment/audio dependent
        return {"src": str(src), "dst": str(dst), "status": "error", "reason": repr(exc)}


def main() -> int:
    args = parse_args()
    try:
        input_dir, output_dir, repo_is_local = validate_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    files = collect_files(input_dir, args.glob)
    if not files:
        print(f"error: no files matched {args.glob!r} under {input_dir}", file=sys.stderr)
        return 2

    print(f"files selected: {len(files)}")
    print(f"mode: {'in-place' if args.in_place else 'copy-to-output-dir'}")
    print(f"trim mode: {'all non-speech' if args.trim_all_nonspeech else 'leading/trailing non-speech'}")
    print(f"hub source: {'local' if repo_is_local else 'torch hub/github'}")
    if args.dry_run:
        for src in files[:20]:
            print(f"  {src} -> {output_for(src, input_dir, output_dir)}")
        if len(files) > 20:
            print(f"  ... {len(files) - 20} more")
        return 0

    if not repo_is_local:
        print("warning: torch.hub may access network/cache to load Silero VAD; this was acknowledged with --allow-download")
    if args.force_reload:
        print("warning: --force-reload may refresh or re-download cached VAD assets")

    try:
        model_and_utils = load_vad_model(args, repo_is_local)
    except Exception as exc:
        print(f"error: failed to load VAD model: {exc!r}", file=sys.stderr)
        return 1

    results = []
    trim_edges_only = not args.trim_all_nonspeech
    for src in files:
        dst = output_for(src, input_dir, output_dir)
        results.append(trim_one(model_and_utils, src, dst, args.force, trim_edges_only, args.use_cuda))

    counts: Dict[str, int] = {}
    filtered: List[str] = []
    for result in results:
        status = str(result["status"])
        counts[status] = counts.get(status, 0) + 1
        if status == "filtered":
            filtered.append(str(result["dst"]))

    print("summary:")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")

    if filtered:
        filtered_file = output_dir / "filtered_files.txt"
        filtered_file.parent.mkdir(parents=True, exist_ok=True)
        filtered_file.write_text("\n".join(filtered) + "\n", encoding="utf-8")
        print(f"filtered file list: {filtered_file}")

    errors = [r for r in results if r["status"] == "error"]
    if errors:
        print("errors:", file=sys.stderr)
        for item in errors[:20]:
            print(f"  - {item['src']} -> {item['dst']}: {item.get('reason')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
