#!/usr/bin/env python3
"""Compute WER/edit-distance summaries for Kaldi-style text files.

Each input line should be: utterance_id token token token ...
"""

from __future__ import annotations

import argparse
from pathlib import Path


def read_key_tokens(path: Path) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            key, *tokens = stripped.split()
            if key in data:
                raise ValueError(f"Duplicate key {key!r} in {path} line {line_no}")
            data[key] = tokens
    return data


def read_utt2spk(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    result: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.strip().split()
            if not parts:
                continue
            if len(parts) != 2:
                raise ValueError(f"Expected 'utt spk' in {path} line {line_no}")
            result[parts[0]] = parts[1]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ref", type=Path, help="Reference text file")
    parser.add_argument("hyp", type=Path, help="Hypothesis text file")
    parser.add_argument("--mode", choices=["strict", "present", "all"], default="strict")
    parser.add_argument("--print-top-wer", action="store_true")
    parser.add_argument("--print-alignments", action="store_true")
    parser.add_argument("--utt2spk", type=Path, help="Optional utterance-to-speaker mapping")
    parser.add_argument("--align-separator", default=" ; ")
    parser.add_argument("--align-empty", default="<eps>")
    args = parser.parse_args()

    import speechbrain.dataio.wer as wer_io
    import speechbrain.utils.edit_distance as edit_distance

    details = edit_distance.wer_details_by_utterance(
        read_key_tokens(args.ref),
        read_key_tokens(args.hyp),
        compute_alignments=args.print_alignments,
        scoring_mode=args.mode,
    )
    summary = edit_distance.wer_summary(details)
    wer_io.print_wer_summary(summary)

    if args.print_top_wer:
        top_non_empty, top_empty = edit_distance.top_wer_utts(details)
        wer_io._print_top_wer_utts(top_non_empty, top_empty)

    utt2spk = read_utt2spk(args.utt2spk)
    if utt2spk:
        by_speaker = edit_distance.wer_details_by_speaker(details, utt2spk)
        top_spks = edit_distance.top_wer_spks(by_speaker)
        wer_io._print_top_wer_spks(top_spks)

    if args.print_alignments:
        wer_io.print_alignments(
            details,
            empty_symbol=args.align_empty,
            separator=args.align_separator,
        )


if __name__ == "__main__":
    main()
