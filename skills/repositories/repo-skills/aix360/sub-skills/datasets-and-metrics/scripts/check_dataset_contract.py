#!/usr/bin/env python3
"""Validate AIX360 dataset file contracts without network or package side effects.

This helper only reads the directory named by --data-dir. It never imports
AIX360 dataset classes, opens a socket, downloads data, installs dependencies,
or extracts archives. Use --fixture for a tiny temporary no-network parser
check. A non-zero exit means the requested local contract is not ready.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


CDC_FILES = [
    "ACQ_H.XPT", "ALQ_H.XPT", "BPQ_H.XPT", "CDQ_H.XPT", "CFQ_H.XPT",
    "CBQ_H.XPT", "CKQ_H.XPT", "HSQ_H.XPT", "DEQ_H.XPT", "DIQ_H.XPT",
    "DBQ_H.XPT", "DLQ_H.XPT", "DUQ_H.XPT", "ECQ_H.XPT", "FSQ_H.XPT",
    "HIQ_H.XPT", "HEQ_H.XPT", "HUQ_H.XPT", "HOQ_H.XPT", "IMQ_H.XPT",
    "INQ_H.XPT", "KIQ_U_H.XPT", "MCQ_H.XPT", "DPQ_H.XPT", "OCQ_H.XPT",
    "OHQ_H.XPT", "OSQ_H.XPT", "PAQ_H.XPT", "PFQ_H.XPT", "RXQASA_H.XPT",
    "RHQ_H.XPT", "SXQ_H.XPT", "SLQ_H.XPT", "SMQFAM_H.XPT", "SMQRTU_H.XPT",
    "SMQSHS_H.XPT", "CSQ_H.XPT", "VTQ_H.XPT", "WHQ_H.XPT", "WHQMEC_H.XPT",
]


def result(dataset: str) -> Dict[str, Any]:
    return {"dataset": dataset, "ok": True, "messages": [], "requirements": []}


def fail(out: Dict[str, Any], message: str) -> None:
    out["ok"] = False
    out["messages"].append("FAIL: " + message)


def note(out: Dict[str, Any], message: str) -> None:
    out["messages"].append("OK: " + message)


def requirement(out: Dict[str, Any], message: str) -> None:
    out["requirements"].append(message)


def require_files(root: Path, names: Iterable[str], out: Dict[str, Any]) -> bool:
    missing = [name for name in names if not (root / name).is_file()]
    if missing:
        fail(out, "missing local file(s): " + ", ".join(missing))
        return False
    note(out, "required local files are present")
    return True


def read_rows(path: Path, delimiter: Optional[str] = ",", limit: int = 5) -> List[List[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        if delimiter == "whitespace":
            return [line.split() for line in handle if line.strip()][:limit]
        return list(csv.reader(handle, delimiter=delimiter))[:limit]


def require_columns(path: Path, columns: Sequence[str], out: Dict[str, Any], delimiter: str = ",") -> bool:
    try:
        rows = read_rows(path, delimiter=delimiter, limit=1)
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(out, f"cannot read {path.name}: {exc}")
        return False
    if not rows:
        fail(out, f"{path.name} is empty; expected a header")
        return False
    header = set(item.strip() for item in rows[0])
    missing = [column for column in columns if column not in header]
    if missing:
        fail(out, f"{path.name} is missing required column(s): {', '.join(missing)}")
        return False
    note(out, f"{path.name} has the required header columns")
    return True


def validate_heloc(root: Path) -> Dict[str, Any]:
    out = result("heloc")
    path = root / "heloc_dataset.csv"
    if require_files(root, [path.name], out):
        require_columns(path, ["RiskPerformance"], out)
        try:
            rows = read_rows(path, delimiter=",", limit=3)
            if len(rows) < 2:
                fail(out, "HELOC CSV has no data rows")
            elif rows[0].index("RiskPerformance") >= len(rows[1]):
                fail(out, "HELOC target column has no value in the first data row")
        except Exception as exc:
            fail(out, f"HELOC row check failed: {exc}")
    requirement(out, "HELOCDataset expects heloc_dataset.csv and performs no schema discovery")
    return out


def validate_compas(root: Path) -> Dict[str, Any]:
    out = result("compas")
    path = root / "compas.csv"
    cols = ["days_b_screening_arrest", "is_recid", "c_charge_degree", "score_text", "c_jail_in", "c_jail_out"]
    if require_files(root, [path.name], out):
        require_columns(path, cols, out)
    requirement(out, "COMPAS default preprocessing parses c_jail_in/c_jail_out as %Y-%m-%d %H:%M:%S")
    return out


def validate_adult(root: Path) -> Dict[str, Any]:
    out = result("adult")
    path = root / "adult.csv"
    if require_files(root, [path.name], out):
        try:
            rows = read_rows(path, delimiter="whitespace", limit=2)
            if not rows or len(rows[0]) < 13:
                fail(out, "Adult raw rows need the positional Census fields")
            else:
                note(out, f"Adult sample row has {len(rows[0])} whitespace fields")
        except Exception as exc:
            fail(out, f"Adult row check failed: {exc}")
    requirement(out, "AdultDataset is a direct-module class and expects a headerless positional file")
    return out


def validate_meps(root: Path) -> Dict[str, Any]:
    out = result("meps")
    path = root / "h181.csv"
    cols = ["RACEV2X", "HISPANX", "SEX", "PERWT15F", "REGION31", "TTLP15X", "TOTEXP15"]
    if require_files(root, [path.name], out):
        require_columns(path, cols, out)
    requirement(out, "MEPS requires the 2015 H181 CSV conversion and current AHRQ usage compliance")
    return out


def validate_ted(root: Path) -> Dict[str, Any]:
    out = result("ted")
    path = root / "Retention.csv"
    if require_files(root, [path.name], out):
        if require_columns(path, ["Y", "E"], out):
            try:
                rows = read_rows(path, delimiter=",", limit=2)
                if len(rows[0]) < 3:
                    fail(out, "TED requires at least one feature column before Y and E")
                if len(rows) < 2:
                    fail(out, "TED CSV has no data rows")
            except Exception as exc:
                fail(out, f"TED row check failed: {exc}")
    requirement(out, "TEDDataset.load_file splits all columns except Y and E into X")
    return out


def validate_mnist(root: Path) -> Dict[str, Any]:
    out = result("mnist")
    names = ["train-images-idx3-ubyte.gz", "t10k-images-idx3-ubyte.gz", "train-labels-idx1-ubyte.gz", "t10k-labels-idx1-ubyte.gz"]
    if require_files(root, names, out):
        for name in names:
            path = root / name
            try:
                with gzip.open(path, "rb") as handle:
                    magic = handle.read(4)
                if len(magic) != 4:
                    fail(out, f"{name} is not a readable gzip payload")
            except (OSError, EOFError) as exc:
                fail(out, f"{name} is not a readable gzip file: {exc}")
        if out["ok"]:
            note(out, "MNIST gzip members are readable")
    requirement(out, "MNISTDataset reads four gzip files and downloads any absent member")
    return out


def json_shape(value: Any, depth: int = 0) -> Tuple[int, ...]:
    if not isinstance(value, list):
        return ()
    if not value:
        return (0,)
    return (len(value),) + json_shape(value[0], depth + 1)


def validate_cifar(root: Path) -> Dict[str, Any]:
    out = result("cifar")
    names = [
        "cifar-10-train1-image.json", "cifar-10-train2-image.json",
        "cifar-10-test-image.json", "cifar-10-train1-label.json",
        "cifar-10-train2-label.json", "cifar-10-test-label.json",
    ]
    if require_files(root, names, out):
        for name in names:
            try:
                with (root / name).open("r", encoding="utf-8") as handle:
                    value = json.load(handle)
                shape = json_shape(value)
                if not shape or shape[0] == 0:
                    fail(out, f"{name} is not a non-empty JSON array")
                else:
                    note(out, f"{name} begins with JSON shape {shape}")
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                fail(out, f"{name} is not valid JSON: {exc}")
    requirement(out, "CIFARDataset expects processed JSON; absent files trigger a verified archive download")
    return out


def validate_celeba(root: Path) -> Dict[str, Any]:
    out = result("celeba")
    imgs = {p.name[:-8] for p in root.glob("*_img.npy") if p.is_file()}
    latents = {p.name[:-11] for p in root.glob("*_latent.npy") if p.is_file()}
    if not imgs:
        fail(out, "no *_img.npy files found")
    paired = sorted(imgs & latents)
    if not paired:
        fail(out, "no image/latent id pair found")
    else:
        note(out, f"found {len(paired)} paired CelebA id(s)")
    requirement(out, "CelebADataset reads paired <id>_img.npy and <id>_latent.npy files")
    return out


def validate_esnli(root: Path) -> Dict[str, Any]:
    out = result("esnli")
    path = root / "docs.jsonl"
    if require_files(root, [path.name], out):
        try:
            with path.open("r", encoding="utf-8") as handle:
                line = next((line.strip() for line in handle if line.strip()), "")
            record = json.loads(line)
            if not isinstance(record, dict) or "docid" not in record:
                fail(out, "first non-empty e-SNLI record must be an object with docid")
            else:
                note(out, "e-SNLI JSONL contains a docid-bearing record")
        except (OSError, UnicodeError, json.JSONDecodeError, StopIteration) as exc:
            fail(out, f"e-SNLI JSONL check failed: {exc}")
    requirement(out, "eSNLIDataset has a fixed docs.jsonl location and no dirpath argument")
    return out


def validate_ford(root: Path) -> Dict[str, Any]:
    out = result("ford")
    names = ["FordA_TRAIN.txt", "FordA_TEST.txt"]
    if require_files(root, names, out):
        for name in names:
            try:
                rows = read_rows(root / name, delimiter="whitespace", limit=3)
                if not rows or any(len(row) != 501 for row in rows):
                    fail(out, f"{name} sample rows must have one label plus 500 values")
                else:
                    note(out, f"{name} has the expected 501-field sample rows")
            except Exception as exc:
                fail(out, f"{name} row check failed: {exc}")
    requirement(out, "FordDataset has fixed cache filenames and may download a ZIP when the train file is absent")
    return out


def validate_sunspots(root: Path) -> Dict[str, Any]:
    out = result("sunspots")
    path = root / "sunspots.csv"
    if require_files(root, [path.name], out):
        try:
            rows = read_rows(path, delimiter=",", limit=3)
            if len(rows) < 2 or len(rows[0]) != 2 or len(rows[1]) != 2:
                fail(out, "sunspots.csv must contain two columns and a data row")
            else:
                note(out, "sunspots.csv has a two-column time/value layout")
        except Exception as exc:
            fail(out, f"sunspots row check failed: {exc}")
    requirement(out, "SunspotDataset returns month/sunspots plus a monthly schema and downloads if absent")
    return out


def validate_climate(root: Path) -> Dict[str, Any]:
    out = result("climate")
    path = root / "jena_climate_2009_2016.csv"
    if require_files(root, [path.name], out):
        try:
            rows = read_rows(path, delimiter=",", limit=1)
            if not rows or "Date Time" not in rows[0] or len(rows[0]) < 15:
                fail(out, "climate CSV needs Date Time plus at least 14 data columns")
            else:
                note(out, "climate CSV has the expected time column and feature width")
        except Exception as exc:
            fail(out, f"climate header check failed: {exc}")
    requirement(out, "ClimateDataset requires TensorFlow and a local fixed-name CSV; it has no dirpath argument")
    return out


def validate_diabetes(root: Path) -> Dict[str, Any]:
    out = result("diabetes")
    path = root / "diabetes.csv"
    if require_files(root, [path.name], out):
        require_columns(path, ["Y"], out)
    requirement(out, "DiabetesDataset expects a cached CSV and otherwise requests a tab-delimited source")
    return out


def validate_cdc(root: Path) -> Dict[str, Any]:
    out = result("cdc")
    present = [name for name in CDC_FILES if (root / name).is_file()]
    missing = [name for name in CDC_FILES if not (root / name).is_file()]
    if missing:
        fail(out, f"missing {len(missing)} of {len(CDC_FILES)} expected NHANES XPT files")
    else:
        note(out, f"all {len(CDC_FILES)} expected NHANES XPT files are present")
    if importlib.util.find_spec("xport") is None:
        requirement(out, "optional dependency xport is absent; conversion cannot run")
    else:
        note(out, "optional dependency xport is discoverable")
    requirement(out, "CDCDataset converts XPT files to csv/ and downloads missing questionnaires")
    return out


def validate_fashion_mnist(root: Path) -> Dict[str, Any]:
    out = result("fashion-mnist")
    cache = root / "FashionMNIST"
    if not cache.is_dir():
        fail(out, "expected FashionMNIST cache directory")
    else:
        raw = cache / "raw"
        processed = cache / "processed"
        if not raw.is_dir() and not processed.is_dir():
            fail(out, "FashionMNIST cache has neither raw nor processed directory")
        else:
            note(out, "FashionMNIST cache layout is present")
    for dep in ("torch", "torchvision"):
        if importlib.util.find_spec(dep) is None:
            requirement(out, f"optional dependency {dep} is absent")
    requirement(out, "FMnistDataset constructs torchvision datasets with download=True")
    return out


VALIDATORS = {
    "adult": validate_adult,
    "cdc": validate_cdc,
    "celeba": validate_celeba,
    "cifar": validate_cifar,
    "climate": validate_climate,
    "compas": validate_compas,
    "diabetes": validate_diabetes,
    "esnli": validate_esnli,
    "fashion-mnist": validate_fashion_mnist,
    "ford": validate_ford,
    "heloc": validate_heloc,
    "meps": validate_meps,
    "mnist": validate_mnist,
    "sunspots": validate_sunspots,
    "ted": validate_ted,
}


def fixture_check() -> Dict[str, Any]:
    """Exercise two local validators against temporary, tiny files."""
    with tempfile.TemporaryDirectory(prefix="aix360-dataset-fixture-") as temp:
        root = Path(temp)
        (root / "heloc_dataset.csv").write_text(
            "ExternalRiskEstimate,RiskPerformance\n50,Good\n20,Bad\n",
            encoding="utf-8",
        )
        (root / "Retention.csv").write_text(
            "feature,Y,E\n1.0,0,0\n2.0,1,1\n", encoding="utf-8"
        )
        checks = [validate_heloc(root), validate_ted(root)]
    ok = all(item["ok"] for item in checks)
    return {"dataset": "fixture", "ok": ok, "messages": ["tiny HELOC and TED fixtures validated"], "details": checks}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only, no-network AIX360 dataset contract validator."
    )
    parser.add_argument("--dataset", choices=sorted(list(VALIDATORS) + ["all"]), help="dataset contract to inspect")
    parser.add_argument("--data-dir", default=".", help="directory containing the expected local files (default: current directory)")
    parser.add_argument("--no-network", action="store_true", default=True, help="assert the safe no-network mode (always enabled)")
    parser.add_argument("--fixture", action="store_true", help="run a tiny temporary HELOC/TED no-network fixture check")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.fixture and not args.dataset:
        print("error: provide --dataset DATASET or use --fixture", file=sys.stderr)
        return 2
    reports: List[Dict[str, Any]] = []
    if args.fixture:
        reports.append(fixture_check())
    if args.dataset:
        root = Path(args.data_dir).expanduser()
        if not root.is_dir():
            report = result(args.dataset)
            fail(report, f"data directory does not exist or is not a directory: {root}")
            reports.append(report)
        else:
            names = sorted(VALIDATORS) if args.dataset == "all" else [args.dataset]
            for name in names:
                reports.append(VALIDATORS[name](root))
    ok = all(item.get("ok", False) for item in reports)
    if args.json:
        print(json.dumps({"no_network": True, "ok": ok, "reports": reports}, indent=2, sort_keys=True))
    else:
        print("NO NETWORK: enabled; no AIX360 dataset constructor was called")
        for report in reports:
            status = "PASS" if report.get("ok") else "FAIL"
            print(f"[{status}] {report['dataset']}")
            for message in report.get("messages", []):
                print(f"  {message}")
            for item in report.get("requirements", []):
                print(f"  REQUIREMENT: {item}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
