#!/usr/bin/env python3
"""Read-only Boltz preprocessing prerequisite checklist."""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Boltz preprocessing prerequisites without starting Redis, "
            "downloading data, running mmseqs, or processing structures."
        )
    )
    parser.add_argument(
        "--targets",
        type=Path,
        help="Processed target directory expected to contain manifest.json and structures/.",
    )
    parser.add_argument(
        "--msa",
        type=Path,
        help="Processed MSA directory expected to contain <msa_id>.npz files.",
    )
    parser.add_argument(
        "--symmetries",
        type=Path,
        help="Ligand symmetry pickle path used by data.symmetries.",
    )
    parser.add_argument(
        "--taxonomy-db",
        type=Path,
        help="taxonomy.rdb file for MSA processing Redis.",
    )
    parser.add_argument(
        "--ccd-db",
        type=Path,
        help="ccd.rdb file for structure processing Redis.",
    )
    parser.add_argument(
        "--ccd-pkl",
        type=Path,
        help="ccd.pkl file used by the clustering stage.",
    )
    parser.add_argument(
        "--clusters",
        type=Path,
        help="clustering.json file used by RCSB/mmCIF processing.",
    )
    parser.add_argument(
        "--raw-msa",
        type=Path,
        help="Raw MSA directory expected to contain .a3m or .a3m.gz files.",
    )
    parser.add_argument(
        "--mmcif",
        type=Path,
        help="Raw mmCIF directory expected to contain .cif or .cif.gz files.",
    )
    parser.add_argument(
        "--mmseqs",
        default="mmseqs",
        help="mmseqs executable name or path to check on PATH.",
    )
    parser.add_argument(
        "--redis-host",
        default="127.0.0.1",
        help="Redis host to probe with a short TCP connection.",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=None,
        help="Optional Redis port to probe. The script never starts Redis.",
    )
    parser.add_argument(
        "--sample-records",
        type=int,
        default=20,
        help="Maximum manifest records to sample when checking MSA references.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of text.",
    )
    return parser.parse_args()


class Report:
    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def add(self, status: str, check: str, detail: str) -> None:
        self.items.append({"status": status, "check": check, "detail": detail})

    @property
    def exit_code(self) -> int:
        return 1 if any(item["status"] == "missing" for item in self.items) else 0

    def print_text(self) -> None:
        labels = {"ok": "OK", "warn": "WARN", "missing": "MISSING"}
        for item in self.items:
            print(f"[{labels[item['status']]}] {item['check']}: {item['detail']}")
        if self.exit_code:
            print("\nNext step: resolve MISSING items before launching expensive preprocessing or training.")
        else:
            print("\nNo missing required items were found by this read-only checklist.")

    def print_json(self) -> None:
        print(json.dumps({"ok": self.exit_code == 0, "checks": self.items}, indent=2))


def describe_path(path: Path) -> str:
    return str(path.expanduser())


def count_files(root: Path, patterns: tuple[str, ...], limit: int = 100_000) -> int:
    count = 0
    for pattern in patterns:
        for _ in root.rglob(pattern):
            count += 1
            if count >= limit:
                return count
    return count


def load_manifest(path: Path, report: Report) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # noqa: BLE001
        report.add("missing", "manifest parse", f"could not parse {describe_path(path)}: {exc}")
        return []

    if isinstance(data, dict) and isinstance(data.get("records"), list):
        records = data["records"]
    elif isinstance(data, list):
        records = data
    else:
        report.add("missing", "manifest schema", "manifest must be a list or an object with records")
        return []

    usable = [record for record in records if isinstance(record, dict) and record.get("id")]
    if not usable:
        report.add("missing", "manifest records", "no records with id values were found")
    else:
        report.add("ok", "manifest records", f"found {len(usable)} record(s)")
    return usable


def check_file(report: Report, label: str, path: Path | None, required: bool = False) -> None:
    if path is None:
        if required:
            report.add("missing", label, "path not provided")
        else:
            report.add("warn", label, "path not provided")
        return
    if path.is_file():
        report.add("ok", label, f"found {describe_path(path)}")
    else:
        report.add("missing" if required else "warn", label, f"not found: {describe_path(path)}")


def check_targets(report: Report, targets: Path | None, msa: Path | None, sample_records: int) -> None:
    if targets is None:
        report.add("warn", "processed targets", "--targets not provided")
        return
    if not targets.is_dir():
        report.add("missing", "processed targets", f"directory not found: {describe_path(targets)}")
        return

    report.add("ok", "processed targets", f"found {describe_path(targets)}")
    structures = targets / "structures"
    records_dir = targets / "records"
    manifest_path = targets / "manifest.json"

    if structures.is_dir():
        npz_count = count_files(structures, ("*.npz",))
        report.add("ok" if npz_count else "missing", "target structures", f"{npz_count} .npz file(s)")
    else:
        report.add("missing", "target structures", f"missing {describe_path(structures)}")

    if records_dir.is_dir():
        json_count = count_files(records_dir, ("*.json",))
        report.add("ok" if json_count else "warn", "target records", f"{json_count} .json file(s)")
    else:
        report.add("warn", "target records", f"missing {describe_path(records_dir)}")

    if not manifest_path.is_file():
        report.add("missing", "manifest", f"missing {describe_path(manifest_path)}")
        return

    report.add("ok", "manifest", f"found {describe_path(manifest_path)}")
    records = load_manifest(manifest_path, report)
    if not records:
        return

    missing_structures: list[str] = []
    missing_msa: list[str] = []
    checked_msa_ids: set[str] = set()
    for record in records[: max(sample_records, 0)]:
        record_id = str(record.get("id"))
        if not (structures / f"{record_id}.npz").is_file():
            missing_structures.append(record_id)
        for chain in record.get("chains", []) or []:
            if not isinstance(chain, dict):
                continue
            msa_id = chain.get("msa_id")
            if msa_id in (None, "", -1, "-1"):
                continue
            msa_id = str(msa_id)
            if msa_id in checked_msa_ids:
                continue
            checked_msa_ids.add(msa_id)
            if msa is not None and msa.is_dir() and not (msa / f"{msa_id}.npz").is_file():
                missing_msa.append(msa_id)

    if missing_structures:
        report.add(
            "missing",
            "sampled structure links",
            "missing structures for record id(s): " + ", ".join(missing_structures[:10]),
        )
    else:
        report.add("ok", "sampled structure links", f"checked {min(len(records), sample_records)} record(s)")

    if msa is None:
        if checked_msa_ids:
            report.add("warn", "sampled MSA links", "MSA ids exist, but --msa was not provided")
    elif not msa.is_dir():
        if checked_msa_ids:
            report.add("missing", "sampled MSA links", "MSA ids exist, but --msa is not a directory")
    elif missing_msa:
        report.add("missing", "sampled MSA links", "missing MSA id(s): " + ", ".join(missing_msa[:10]))
    elif checked_msa_ids:
        report.add("ok", "sampled MSA links", f"checked {len(checked_msa_ids)} unique MSA id(s)")
    else:
        report.add("warn", "sampled MSA links", "no non-empty MSA ids found in sampled records")


def check_msa(report: Report, msa: Path | None) -> None:
    if msa is None:
        report.add("warn", "processed MSA", "--msa not provided")
        return
    if not msa.is_dir():
        report.add("missing", "processed MSA", f"directory not found: {describe_path(msa)}")
        return
    count = count_files(msa, ("*.npz",))
    report.add("ok" if count else "warn", "processed MSA", f"{count} .npz file(s) in {describe_path(msa)}")


def check_raw_inputs(report: Report, raw_msa: Path | None, mmcif: Path | None) -> None:
    if raw_msa is not None:
        if raw_msa.is_dir():
            count = count_files(raw_msa, ("*.a3m", "*.a3m.gz"))
            report.add("ok" if count else "warn", "raw MSA", f"{count} .a3m/.a3m.gz file(s)")
        else:
            report.add("missing", "raw MSA", f"directory not found: {describe_path(raw_msa)}")
    if mmcif is not None:
        if mmcif.is_dir():
            count = count_files(mmcif, ("*.cif", "*.cif.gz"))
            report.add("ok" if count else "warn", "raw mmCIF", f"{count} .cif/.cif.gz file(s)")
        else:
            report.add("missing", "raw mmCIF", f"directory not found: {describe_path(mmcif)}")


def check_executable(report: Report, executable: str) -> None:
    found = shutil.which(executable)
    if found:
        report.add("ok", "mmseqs executable", f"found {found}")
    else:
        report.add("warn", "mmseqs executable", f"not found on PATH or not executable: {executable}")


def check_redis(report: Report, host: str, port: int | None) -> None:
    if port is None:
        report.add("warn", "Redis port", "--redis-port not provided; no TCP probe attempted")
        return
    try:
        with socket.create_connection((host, port), timeout=1.0):
            report.add("ok", "Redis TCP", f"connection accepted at {host}:{port}")
    except OSError as exc:
        report.add("warn", "Redis TCP", f"no connection at {host}:{port}: {exc}")


def main() -> int:
    args = parse_args()
    report = Report()

    check_targets(report, args.targets, args.msa, args.sample_records)
    check_msa(report, args.msa)
    check_file(report, "symmetry pickle", args.symmetries)
    check_file(report, "taxonomy Redis DB", args.taxonomy_db)
    check_file(report, "CCD Redis DB", args.ccd_db)
    check_file(report, "CCD pickle", args.ccd_pkl)
    check_file(report, "cluster map", args.clusters)
    check_raw_inputs(report, args.raw_msa, args.mmcif)
    check_executable(report, args.mmseqs)
    check_redis(report, args.redis_host, args.redis_port)

    if args.json:
        report.print_json()
    else:
        report.print_text()
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
