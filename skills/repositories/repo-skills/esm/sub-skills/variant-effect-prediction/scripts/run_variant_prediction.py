#!/usr/bin/env python3
"""Run zero-shot ESM variant-effect prediction for a DMS CSV.

This skill-owned runner follows the fair-esm variant prediction example contract
while avoiding source-checkout dependencies and supporting CPU execution when
`--nogpu` is set. Full inference can still download model weights and may be
expensive.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import string
from pathlib import Path
from typing import Iterable, Sequence

import torch

import esm

INSERTION_TRANSLATION = str.maketrans({character: None for character in string.ascii_lowercase + ".*"})


def remove_insertions(sequence: str) -> str:
    return sequence.translate(INSERTION_TRANSLATION)


def read_msa(filename: Path, nseq: int) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    current_label: str | None = None
    current_sequence: list[str] = []

    def flush() -> None:
        nonlocal current_label, current_sequence
        if current_label is not None:
            records.append((current_label, remove_insertions("".join(current_sequence))))
        current_label = None
        current_sequence = []

    with filename.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                flush()
                current_label = line[1:].strip() or f"seq{len(records) + 1}"
            elif current_label is not None:
                current_sequence.append(line)
    flush()
    return records[:nseq]


def read_dms_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("DMS CSV must include a header row")
        return list(reader.fieldnames), list(reader)


def write_dms_rows(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def mutation_parts(mutation: str, sequence: str, offset_idx: int) -> tuple[str, int, str]:
    if len(mutation) < 3:
        raise ValueError(f"invalid mutation {mutation!r}; expected form like A24D")
    wt = mutation[0]
    mt = mutation[-1]
    try:
        idx = int(mutation[1:-1]) - offset_idx
    except ValueError as exc:
        raise ValueError(f"invalid mutation {mutation!r}; expected numeric position") from exc
    if idx < 0 or idx >= len(sequence):
        raise ValueError(f"mutation {mutation!r} maps to sequence index {idx}; check --offset-idx")
    if sequence[idx] != wt:
        raise ValueError(
            f"mutation {mutation!r} expects wild-type {wt} at sequence index {idx}, "
            f"but --sequence has {sequence[idx]!r}"
        )
    return wt, idx, mt


def label_row(mutation: str, sequence: str, token_probs: torch.Tensor, alphabet, offset_idx: int) -> float:
    wt, idx, mt = mutation_parts(mutation, sequence, offset_idx)
    wt_encoded = alphabet.get_idx(wt)
    mt_encoded = alphabet.get_idx(mt)
    return (token_probs[0, 1 + idx, mt_encoded] - token_probs[0, 1 + idx, wt_encoded]).item()


def compute_pppl(mutation: str, sequence: str, model, alphabet, offset_idx: int, device: torch.device) -> float:
    _, idx, mt = mutation_parts(mutation, sequence, offset_idx)
    mutated = sequence[:idx] + mt + sequence[idx + 1 :]
    batch_converter = alphabet.get_batch_converter()
    _, _, batch_tokens = batch_converter([("protein1", mutated)])
    batch_tokens = batch_tokens.to(device)

    log_probs: list[float] = []
    for token_index in range(1, len(mutated) - 1):
        masked_tokens = batch_tokens.clone()
        masked_tokens[0, token_index] = alphabet.mask_idx
        with torch.no_grad():
            token_probs = torch.log_softmax(model(masked_tokens)["logits"], dim=-1)
        log_probs.append(token_probs[0, token_index, alphabet.get_idx(mutated[token_index])].item())
    return sum(log_probs)


def score_with_msa_transformer(args, model, alphabet, rows: list[dict[str, str]], device: torch.device) -> list[float]:
    if args.scoring_strategy != "masked-marginals":
        raise ValueError("MSA Transformer only supports masked-marginals")
    if args.msa_path is None:
        raise ValueError("MSA Transformer runs require --msa-path")

    batch_converter = alphabet.get_batch_converter()
    msa = read_msa(args.msa_path, args.msa_samples)
    if not msa:
        raise ValueError(f"MSA path has no readable records: {args.msa_path}")
    _, _, batch_tokens = batch_converter([msa])
    batch_tokens = batch_tokens.to(device)

    token_prob_columns: list[torch.Tensor] = []
    for token_index in range(batch_tokens.size(2)):
        masked_tokens = batch_tokens.clone()
        masked_tokens[0, 0, token_index] = alphabet.mask_idx
        with torch.no_grad():
            token_probs = torch.log_softmax(model(masked_tokens)["logits"], dim=-1)
        token_prob_columns.append(token_probs[:, 0, token_index].detach().cpu())
    token_probs = torch.cat(token_prob_columns, dim=0).unsqueeze(0)

    return [label_row(row[args.mutation_col], args.sequence, token_probs, alphabet, args.offset_idx) for row in rows]


def score_with_sequence_model(args, model, alphabet, rows: list[dict[str, str]], device: torch.device) -> list[float]:
    batch_converter = alphabet.get_batch_converter()
    _, _, batch_tokens = batch_converter([("protein1", args.sequence)])
    batch_tokens = batch_tokens.to(device)

    if args.scoring_strategy == "wt-marginals":
        with torch.no_grad():
            token_probs = torch.log_softmax(model(batch_tokens)["logits"], dim=-1).detach().cpu()
        return [label_row(row[args.mutation_col], args.sequence, token_probs, alphabet, args.offset_idx) for row in rows]

    if args.scoring_strategy == "masked-marginals":
        token_prob_columns: list[torch.Tensor] = []
        for token_index in range(batch_tokens.size(1)):
            masked_tokens = batch_tokens.clone()
            masked_tokens[0, token_index] = alphabet.mask_idx
            with torch.no_grad():
                token_probs = torch.log_softmax(model(masked_tokens)["logits"], dim=-1)
            token_prob_columns.append(token_probs[:, token_index].detach().cpu())
        token_probs = torch.cat(token_prob_columns, dim=0).unsqueeze(0)
        return [label_row(row[args.mutation_col], args.sequence, token_probs, alphabet, args.offset_idx) for row in rows]

    if args.scoring_strategy == "pseudo-ppl":
        return [compute_pppl(row[args.mutation_col], args.sequence, model, alphabet, args.offset_idx, device) for row in rows]

    raise ValueError(f"unsupported scoring strategy: {args.scoring_strategy}")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score DMS mutations with fair-esm sequence or MSA models.")
    parser.add_argument("--model-location", nargs="+", required=True, help="model names or local checkpoint paths")
    parser.add_argument("--sequence", required=True, help="wild-type sequence used by mutation notation")
    parser.add_argument("--dms-input", type=Path, required=True, help="input DMS CSV")
    parser.add_argument("--mutation-col", default="mutant", help="CSV column containing mutations such as A24D")
    parser.add_argument("--dms-output", type=Path, required=True, help="output CSV path")
    parser.add_argument("--offset-idx", type=int, default=0, help="residue numbering offset")
    parser.add_argument(
        "--scoring-strategy",
        choices=["wt-marginals", "pseudo-ppl", "masked-marginals"],
        default="wt-marginals",
        help="prediction scoring strategy",
    )
    parser.add_argument("--msa-path", type=Path, help="A3M/FASTA MSA path for MSA Transformer")
    parser.add_argument("--msa-samples", type=int, default=400, help="number of MSA records to read")
    parser.add_argument("--nogpu", action="store_true", help="force CPU execution")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    args.sequence = args.sequence.strip().upper()
    fieldnames, rows = read_dms_rows(args.dms_input)
    if args.mutation_col not in fieldnames:
        raise ValueError(f"mutation column {args.mutation_col!r} not found in DMS CSV")

    device = torch.device("cuda" if torch.cuda.is_available() and not args.nogpu else "cpu")
    output_fields = list(fieldnames)

    for model_location in args.model_location:
        model, alphabet = esm.pretrained.load_model_and_alphabet(model_location)
        model.eval().to(device)

        if isinstance(model, esm.MSATransformer):
            scores = score_with_msa_transformer(args, model, alphabet, rows, device)
        else:
            scores = score_with_sequence_model(args, model, alphabet, rows, device)

        output_column = Path(model_location).stem if str(model_location).endswith(".pt") else str(model_location)
        if output_column not in output_fields:
            output_fields.append(output_column)
        for row, score in zip(rows, scores):
            row[output_column] = f"{score:.8g}" if math.isfinite(score) else str(score)

    write_dms_rows(args.dms_output, output_fields, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
