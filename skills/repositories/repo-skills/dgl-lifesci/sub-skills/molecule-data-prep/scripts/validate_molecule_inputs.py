#!/usr/bin/env python3
"""Validate small DGL-LifeSci SMILES CSV/TXT fixtures without downloads."""

import argparse
import csv
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Validate CSV/TXT SMILES fixtures for DGL-LifeSci data prep and "
            "optionally report DGL graph node/feature shapes."
        )
    )
    parser.add_argument("--input", required=True, help="Path to a CSV or TXT fixture.")
    parser.add_argument(
        "--smiles-column",
        default=None,
        help="CSV column containing SMILES strings. Required for --format csv.",
    )
    parser.add_argument(
        "--tasks",
        default=None,
        help="Comma-separated CSV label columns to validate. Defaults to all non-SMILES columns.",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "txt"),
        required=True,
        help="Input file format.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Maximum number of data rows to validate.",
    )
    parser.add_argument(
        "--require-labels",
        action="store_true",
        help="Fail when any selected task label is missing or non-numeric. CSV only.",
    )
    parser.add_argument(
        "--graph",
        choices=("bigraph", "complete"),
        default=None,
        help="Optionally construct DGL graphs and report feature shapes.",
    )
    return parser.parse_args()


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def import_dependencies(require_graph):
    try:
        from rdkit import Chem
    except Exception as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(f"failed to import RDKit: {exc}") from exc

    graph_api = None
    if require_graph:
        try:
            from dgllife.utils import (
                CanonicalAtomFeaturizer,
                CanonicalBondFeaturizer,
                smiles_to_bigraph,
                smiles_to_complete_graph,
            )
        except Exception as exc:  # pragma: no cover - environment-specific
            raise RuntimeError(f"failed to import DGL-LifeSci graph utilities: {exc}") from exc
        graph_api = {
            "CanonicalAtomFeaturizer": CanonicalAtomFeaturizer,
            "CanonicalBondFeaturizer": CanonicalBondFeaturizer,
            "bigraph": smiles_to_bigraph,
            "complete": smiles_to_complete_graph,
        }
    return Chem, graph_api


def read_csv_rows(path, smiles_column, tasks, max_rows):
    if smiles_column is None:
        raise ValueError("--smiles-column is required for CSV input")
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")
        missing = [name for name in [smiles_column] if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
        if tasks is None:
            task_names = [name for name in reader.fieldnames if name != smiles_column]
        else:
            task_names = [name.strip() for name in tasks.split(",") if name.strip()]
            absent_tasks = [name for name in task_names if name not in reader.fieldnames]
            if absent_tasks:
                raise ValueError(f"CSV is missing task column(s): {', '.join(absent_tasks)}")
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if max_rows is not None and len(rows) >= max_rows:
                break
            rows.append(
                {
                    "row_number": row_number,
                    "smiles": (row.get(smiles_column) or "").strip(),
                    "labels": {task: (row.get(task) or "").strip() for task in task_names},
                }
            )
    return rows, task_names


def read_txt_rows(path, max_rows):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for row_number, line in enumerate(handle, start=1):
            if max_rows is not None and len(rows) >= max_rows:
                break
            rows.append({"row_number": row_number, "smiles": line.strip(), "labels": {}})
    return rows, []


def validate_label(value):
    if value == "":
        return False
    try:
        float(value)
    except ValueError:
        return False
    return True


def tensor_shape(value):
    if hasattr(value, "shape"):
        return tuple(int(dim) for dim in value.shape)
    if hasattr(value, "size"):
        size = value.size()
        return tuple(int(dim) for dim in size)
    return None


def graph_summary(graph):
    node_shapes = {key: tensor_shape(value) for key, value in graph.ndata.items()}
    edge_shapes = {key: tensor_shape(value) for key, value in graph.edata.items()}
    return {
        "nodes": int(graph.num_nodes()),
        "edges": int(graph.num_edges()),
        "node_features": node_shapes,
        "edge_features": edge_shapes,
    }


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_file():
        return fail(f"input file does not exist: {input_path}")
    if args.max_rows is not None and args.max_rows <= 0:
        return fail("--max-rows must be positive when provided")
    if args.format == "txt" and args.require_labels:
        return fail("--require-labels is only valid for CSV input")

    try:
        Chem, graph_api = import_dependencies(args.graph is not None)
    except RuntimeError as exc:
        return fail(str(exc))

    try:
        if args.format == "csv":
            rows, task_names = read_csv_rows(input_path, args.smiles_column, args.tasks, args.max_rows)
        else:
            rows, task_names = read_txt_rows(input_path, args.max_rows)
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    if not rows:
        return fail("no data rows were found")

    node_featurizer = edge_featurizer = graph_constructor = None
    if graph_api is not None:
        node_featurizer = graph_api["CanonicalAtomFeaturizer"]()
        edge_featurizer = graph_api["CanonicalBondFeaturizer"]() if args.graph == "bigraph" else None
        graph_constructor = graph_api[args.graph]

    invalid_rows = []
    missing_label_rows = []
    graph_failures = []
    graph_summaries = []
    valid_count = 0

    for row in rows:
        row_number = row["row_number"]
        smiles = row["smiles"]
        if smiles == "":
            invalid_rows.append((row_number, smiles, "empty SMILES"))
            continue
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_rows.append((row_number, smiles, "RDKit could not parse SMILES"))
            continue
        valid_count += 1

        if args.require_labels:
            for task_name, value in row["labels"].items():
                if not validate_label(value):
                    missing_label_rows.append((row_number, task_name, value))

        if graph_constructor is not None:
            try:
                graph = graph_constructor(
                    smiles,
                    node_featurizer=node_featurizer,
                    edge_featurizer=edge_featurizer,
                )
            except Exception as exc:  # pragma: no cover - dependency-specific error type
                graph_failures.append((row_number, smiles, f"graph construction failed: {exc}"))
            else:
                if graph is None:
                    graph_failures.append((row_number, smiles, "graph constructor returned None"))
                else:
                    graph_summaries.append((row_number, smiles, graph_summary(graph)))

    print(f"input: {input_path}")
    print(f"format: {args.format}")
    print(f"rows_checked: {len(rows)}")
    print(f"valid_smiles: {valid_count}")
    print(f"invalid_smiles: {len(invalid_rows)}")
    if task_names:
        print(f"tasks: {', '.join(task_names)}")
    if args.graph:
        print(f"graph: {args.graph}")
        for row_number, smiles, summary in graph_summaries[:5]:
            print(
                "graph_summary: "
                f"row={row_number} smiles={smiles} nodes={summary['nodes']} "
                f"edges={summary['edges']} node_features={summary['node_features']} "
                f"edge_features={summary['edge_features']}"
            )
        if len(graph_summaries) > 5:
            print(f"graph_summary: ... {len(graph_summaries) - 5} more valid graph(s)")

    for row_number, smiles, reason in invalid_rows:
        print(f"invalid_row: row={row_number} smiles={smiles!r} reason={reason}", file=sys.stderr)
    for row_number, task_name, value in missing_label_rows:
        print(
            f"label_error: row={row_number} task={task_name} value={value!r} reason=missing-or-non-numeric",
            file=sys.stderr,
        )
    for row_number, smiles, reason in graph_failures:
        print(f"graph_error: row={row_number} smiles={smiles!r} reason={reason}", file=sys.stderr)

    if invalid_rows or missing_label_rows or graph_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
