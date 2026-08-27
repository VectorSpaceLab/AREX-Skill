#!/usr/bin/env python3
"""Validate HelixFold3 and HelixFold-S1 entity JSON without running inference."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ENTITY_TYPES = {"protein", "dna", "rna", "ligand", "ion"}
POLYMER_TYPES = {"protein", "dna", "rna"}
PROTEIN_ALPHABET = set("ABCDEFGHIKLMNPQRSTVWXYZJUO")
DNA_ALPHABET = set("ACGTN")
RNA_ALPHABET = set("ACGUN")
SAFE_JOB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
ENTITY_REF = re.compile(r"^(\d+)-(\d+)(?:-(\d+))?$")


class Finding:
    def __init__(self, level: str, path: str, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"level": self.level, "path": self.path, "message": self.message}

    def format(self) -> str:
        return f"[{self.level}] {self.path}: {self.message}"


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def add(finding_list: List[Finding], level: str, path: str, message: str) -> None:
    finding_list.append(Finding(level, path, message))


def validate_sequence(
    sequence: Any,
    entity_type: str,
    path: str,
    strict_sequence_alphabet: bool,
    findings: List[Finding],
) -> int:
    if not isinstance(sequence, str) or not sequence:
        add(findings, "error", path, "polymer entity requires a non-empty sequence string")
        return 0

    normalized = sequence.replace(" ", "").replace("\n", "").upper()
    if normalized != sequence.upper():
        add(findings, "warning", path, "sequence contains whitespace; model preprocessing may not accept it")

    if entity_type == "protein":
        alphabet = PROTEIN_ALPHABET
        alphabet_name = "protein one-letter alphabet"
    elif entity_type == "dna":
        alphabet = DNA_ALPHABET
        alphabet_name = "DNA alphabet A/C/G/T/N"
    else:
        alphabet = RNA_ALPHABET
        alphabet_name = "RNA alphabet A/C/G/U/N"

    invalid = sorted(set(normalized) - alphabet)
    if invalid:
        level = "error" if strict_sequence_alphabet else "warning"
        add(
            findings,
            level,
            path,
            f"sequence contains characters outside the {alphabet_name}: {''.join(invalid)}",
        )
    return len(normalized)


def validate_modifications(
    entity: Dict[str, Any],
    entity_type: str,
    sequence_length: int,
    mode: str,
    entity_path: str,
    findings: List[Finding],
) -> None:
    if "modification" not in entity:
        return

    mods = entity["modification"]
    path = f"{entity_path}.modification"
    if entity_type not in POLYMER_TYPES:
        add(findings, "error", path, "modification is only valid for protein, dna, or rna entities")
        return
    if not isinstance(mods, list):
        add(findings, "error", path, "modification must be a list")
        return

    seen_indices = set()
    for index, mod in enumerate(mods):
        mod_path = f"{path}[{index}]"
        if not isinstance(mod, dict):
            add(findings, "error", mod_path, "modification item must be an object")
            continue

        mod_type = mod.get("type")
        if not isinstance(mod_type, str) or not mod_type:
            add(findings, "error", f"{mod_path}.type", "modification requires a non-empty type string")
        elif mod_type == "residue_replace":
            if not isinstance(mod.get("ccd"), str) or not mod.get("ccd"):
                add(findings, "error", f"{mod_path}.ccd", "residue_replace requires a non-empty CCD code")
        elif mode == "helixfold-s1" and mod_type == "sidechain_replace":
            if not isinstance(mod.get("R_smiles"), str) or not mod.get("R_smiles"):
                add(findings, "error", f"{mod_path}.R_smiles", "sidechain_replace requires R_smiles in S1 inputs")
            if "R_connect_idx" not in mod or not is_nonnegative_int(mod.get("R_connect_idx")):
                add(findings, "error", f"{mod_path}.R_connect_idx", "sidechain_replace requires a non-negative integer R_connect_idx")
        else:
            add(
                findings,
                "error",
                f"{mod_path}.type",
                f"unsupported modification type {mod_type!r} for {mode}",
            )

        residue_index = mod.get("index")
        if not is_positive_int(residue_index):
            add(findings, "error", f"{mod_path}.index", "modification index must be a 1-based positive integer")
        elif sequence_length and residue_index > sequence_length:
            add(
                findings,
                "error",
                f"{mod_path}.index",
                f"modification index {residue_index} exceeds sequence length {sequence_length}",
            )
        elif residue_index in seen_indices:
            add(findings, "error", f"{mod_path}.index", f"duplicate modification index {residue_index}")
        else:
            seen_indices.add(residue_index)


def validate_entity(
    entity: Any,
    index: int,
    mode: str,
    strict_sequence_alphabet: bool,
    findings: List[Finding],
) -> Tuple[int, int, Dict[str, int]]:
    entity_path = f"entities[{index}]"
    token_count = 0
    expanded_chain_count = 0
    type_counts: Dict[str, int] = {}

    if not isinstance(entity, dict):
        add(findings, "error", entity_path, "entity must be an object")
        return token_count, expanded_chain_count, type_counts

    entity_type = entity.get("type")
    if not isinstance(entity_type, str) or entity_type not in ENTITY_TYPES:
        add(findings, "error", f"{entity_path}.type", f"type must be one of {sorted(ENTITY_TYPES)}")
        return token_count, expanded_chain_count, type_counts

    count = entity.get("count")
    if not is_positive_int(count):
        add(findings, "error", f"{entity_path}.count", "count must be a positive integer")
        count = 0
    else:
        if mode == "helixfold-s1" and count > 50:
            add(findings, "error", f"{entity_path}.count", "HelixFold-S1 native schema limits count to at most 50")
        expanded_chain_count += count
        type_counts[entity_type] = count

    if entity_type in POLYMER_TYPES:
        sequence_length = validate_sequence(
            entity.get("sequence"),
            entity_type,
            f"{entity_path}.sequence",
            strict_sequence_alphabet,
            findings,
        )
        token_count += sequence_length * count
        if "ccd" in entity or "smiles" in entity:
            add(findings, "warning", entity_path, "polymer entities should not use ligand ccd/smiles fields")
        validate_modifications(entity, entity_type, sequence_length, mode, entity_path, findings)
    elif entity_type == "ligand":
        has_ccd = isinstance(entity.get("ccd"), str) and bool(entity.get("ccd"))
        has_smiles = isinstance(entity.get("smiles"), str) and bool(entity.get("smiles"))
        if not has_ccd and not has_smiles:
            add(findings, "error", entity_path, "ligand requires a non-empty ccd or smiles field")
        elif has_ccd and has_smiles:
            add(findings, "warning", entity_path, "both ccd and smiles are present; native preprocessing prefers ccd and may ignore smiles")
        if "sequence" in entity:
            add(findings, "warning", entity_path, "ligand entities should not include sequence")
        if "modification" in entity:
            add(findings, "error", f"{entity_path}.modification", "ligands do not support polymer modifications")
    elif entity_type == "ion":
        if not isinstance(entity.get("ccd"), str) or not entity.get("ccd"):
            add(findings, "error", f"{entity_path}.ccd", "ion requires a non-empty CCD code")
        if "smiles" in entity:
            add(findings, "error", f"{entity_path}.smiles", "ion entities should use ccd, not smiles")
        if "sequence" in entity:
            add(findings, "warning", entity_path, "ion entities should not include sequence")
        if "modification" in entity:
            add(findings, "error", f"{entity_path}.modification", "ions do not support polymer modifications")

    known_fields = {"type", "sequence", "count", "ccd", "smiles", "modification"}
    if mode == "helixfold-s1":
        known_fields.update({"name"})
    unknown = sorted(set(entity) - known_fields)
    if unknown:
        add(findings, "warning", entity_path, f"unrecognized entity fields: {', '.join(unknown)}")

    return token_count, expanded_chain_count, type_counts


def parse_entity_ref(value: Any) -> Optional[Tuple[int, int, Optional[int]]]:
    if not isinstance(value, str):
        return None
    match = ENTITY_REF.match(value)
    if not match:
        return None
    entity_index = int(match.group(1))
    chain_index = int(match.group(2))
    residue_index = int(match.group(3)) if match.group(3) is not None else None
    if entity_index <= 0 or chain_index <= 0 or (residue_index is not None and residue_index <= 0):
        return None
    return entity_index, chain_index, residue_index


def validate_entity_ref(
    value: Any,
    path: str,
    entities: List[Any],
    require_residue: bool,
    findings: List[Finding],
) -> None:
    parsed = parse_entity_ref(value)
    if parsed is None:
        expected = "<entity>-<copy>-<residue>" if require_residue else "<entity>-<copy>"
        add(findings, "error", path, f"entity reference must use positive 1-based {expected} format")
        return

    entity_index, chain_index, residue_index = parsed
    if entity_index > len(entities):
        add(findings, "error", path, f"entity index {entity_index} exceeds entity count {len(entities)}")
        return

    entity = entities[entity_index - 1]
    if not isinstance(entity, dict):
        return

    count = entity.get("count")
    if is_positive_int(count) and chain_index > count:
        add(findings, "error", path, f"copy index {chain_index} exceeds entity count {count}")

    if require_residue:
        if residue_index is None:
            add(findings, "error", path, "residue-level constraint requires a residue index")
        elif isinstance(entity.get("sequence"), str) and residue_index > len(entity["sequence"]):
            add(findings, "error", path, f"residue index {residue_index} exceeds sequence length {len(entity['sequence'])}")
    elif residue_index is not None:
        add(findings, "warning", path, "S1 sample constraints ignore residue indices; use <entity>-<copy>")


def validate_constraints(data: Dict[str, Any], mode: str, entities: List[Any], findings: List[Finding]) -> None:
    if "constraint" in data and mode == "helixfold-s1" and data.get("constraint"):
        add(findings, "error", "constraint", "constraint is not supported by HelixFold-S1; use s1_sample_constraint")

    if "s1_sample_constraint" in data and mode != "helixfold-s1" and data.get("s1_sample_constraint"):
        add(findings, "error", "s1_sample_constraint", "s1_sample_constraint is only supported in --mode helixfold-s1")

    if "s1_sample_constraint" not in data:
        return

    constraints = data["s1_sample_constraint"]
    if not isinstance(constraints, list):
        add(findings, "error", "s1_sample_constraint", "s1_sample_constraint must be a list")
        return
    if len(constraints) > 10:
        add(findings, "error", "s1_sample_constraint", "S1 supports at most 10 sample constraints")

    for index, constraint in enumerate(constraints):
        constraint_path = f"s1_sample_constraint[{index}]"
        if not isinstance(constraint, dict):
            add(findings, "error", constraint_path, "constraint item must be an object")
            continue
        unknown = sorted(set(constraint) - {"left_entity", "right_entity"})
        if unknown:
            add(findings, "error", constraint_path, f"unrecognized S1 sample constraint fields: {', '.join(unknown)}")
        left = constraint.get("left_entity")
        right = constraint.get("right_entity")
        if left == right:
            add(findings, "error", constraint_path, "left_entity and right_entity must not be the same")
        validate_entity_ref(left, f"{constraint_path}.left_entity", entities, False, findings)
        validate_entity_ref(right, f"{constraint_path}.right_entity", entities, False, findings)


def validate_top_level(data: Any, mode: str, findings: List[Finding]) -> List[Any]:
    if not isinstance(data, dict):
        add(findings, "error", "$", "input must be a JSON object")
        return []

    if mode == "helixfold-s1":
        job_name = data.get("job_name")
        if not isinstance(job_name, str) or not job_name:
            add(findings, "error", "job_name", "HelixFold-S1 input requires a non-empty job_name")
        else:
            if len(job_name) > 200:
                add(findings, "error", "job_name", "HelixFold-S1 native schema limits job_name to at most 200 characters")
            if not SAFE_JOB_NAME.match(job_name):
                add(findings, "warning", "job_name", "job_name should contain only letters, numbers, underscore, dot, or dash")

        for field in ("recycle", "ensemble"):
            if field in data:
                if not is_positive_int(data[field]):
                    add(findings, "error", field, f"{field} must be a positive integer when present")
                elif data[field] > 100:
                    add(findings, "error", field, f"{field} is above the native schema maximum of 100")

        model_type = data.get("model_type")
        if model_type is None:
            add(findings, "error", "model_type", "HelixFold-S1 native schema requires model_type: HelixFold-S1")
        elif model_type != "HelixFold-S1":
            add(findings, "error", "model_type", "expected HelixFold-S1 for S1 planning")
    else:
        for field in ("job_name", "recycle", "ensemble", "s1_sample_constraint"):
            if field in data:
                add(findings, "warning", field, f"{field} is S1-specific and is ignored for HelixFold3 planning")

        model_type = data.get("model_type")
        if model_type is not None and model_type != "HelixFold3":
            add(findings, "warning", "model_type", "expected HelixFold3 for HelixFold3 planning")

    entities = data.get("entities")
    if not isinstance(entities, list) or not entities:
        add(findings, "error", "entities", "entities must be a non-empty list")
        return []
    return entities


def validate(data: Any, args: argparse.Namespace) -> Dict[str, Any]:
    findings: List[Finding] = []
    entities = validate_top_level(data, args.mode, findings)

    polymer_tokens = 0
    expanded_chains = 0
    type_counts: Dict[str, int] = {entity_type: 0 for entity_type in sorted(ENTITY_TYPES)}

    for index, entity in enumerate(entities):
        tokens, chains, counts = validate_entity(
            entity,
            index,
            args.mode,
            args.strict_sequence_alphabet,
            findings,
        )
        polymer_tokens += tokens
        expanded_chains += chains
        for entity_type, count in counts.items():
            type_counts[entity_type] += count

    if isinstance(data, dict):
        validate_constraints(data, args.mode, entities, findings)

    if args.mode == "helixfold-s1" and expanded_chains and expanded_chains < 2:
        add(findings, "error", "entities", "HelixFold-S1 README warns that at least two chains are required")

    if args.max_tokens is not None and polymer_tokens > args.max_tokens:
        add(
            findings,
            "warning",
            "entities",
            f"expanded polymer token count {polymer_tokens} exceeds --max-tokens {args.max_tokens}",
        )

    if polymer_tokens >= 1000:
        add(
            findings,
            "warning",
            "entities",
            "expanded polymer tokens are near documented 32 GB GPU planning limits; ligand/nucleic-acid atoms may add memory pressure",
        )

    errors = [finding for finding in findings if finding.level == "error"]
    warnings = [finding for finding in findings if finding.level == "warning"]

    return {
        "ok": not errors,
        "mode": args.mode,
        "summary": {
            "entity_count": len(entities),
            "expanded_chain_count": expanded_chains,
            "expanded_polymer_tokens": polymer_tokens,
            "type_counts": {k: v for k, v in type_counts.items() if v},
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "findings": [finding.to_dict() for finding in findings],
    }


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"error: file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate HelixFold3 or HelixFold-S1 entity JSON without downloads or inference."
    )
    parser.add_argument("json_path", type=Path, help="Path to the input JSON file to validate.")
    parser.add_argument(
        "--mode",
        choices=("helixfold3", "helixfold-s1"),
        default="helixfold3",
        help="Validation mode. Use helixfold-s1 for S1 top-level fields and multi-chain checks.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Warn when expanded polymer token count exceeds this planning threshold.",
    )
    parser.add_argument(
        "--strict-sequence-alphabet",
        action="store_true",
        help="Treat non-standard sequence characters as errors instead of warnings.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    if args.max_tokens is not None and args.max_tokens <= 0:
        raise SystemExit("error: --max-tokens must be positive")

    data = load_json(args.json_path)
    report = validate(data, args)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"mode: {report['mode']}")
        print(f"ok: {str(report['ok']).lower()}")
        print(f"entity_count: {summary['entity_count']}")
        print(f"expanded_chain_count: {summary['expanded_chain_count']}")
        print(f"expanded_polymer_tokens: {summary['expanded_polymer_tokens']}")
        if summary["type_counts"]:
            print("type_counts: " + ", ".join(f"{k}={v}" for k, v in sorted(summary["type_counts"].items())))
        for finding in report["findings"]:
            print(Finding(finding["level"], finding["path"], finding["message"]).format())

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
