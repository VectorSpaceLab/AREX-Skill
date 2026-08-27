#!/usr/bin/env python3
"""Safe core PaddleHelix API diagnostics.

This helper performs tiny import/data checks. It does not download data, train
models, or require a PaddleHelix checkout unless --repo-root is provided.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Callable, Iterable


OPTIONAL_HINTS = {
    "numpy": "Install NumPy before running dataset, splitter, or molecule-array checks.",
    "pgl": "Install a PGL version compatible with the selected PaddlePaddle backend, or avoid InMemoryDataset graph dataloaders and featurizer/model paths.",
    "paddle": "Install a compatible PaddlePaddle CPU/GPU package before importing model_zoo or running training/inference code.",
    "rdkit": "Install RDKit before using scaffold splitters or compound graph utilities.",
    "sklearn": "Install scikit-learn; legacy setup metadata may still use the deprecated package name sklearn.",
}


class CheckFailure(RuntimeError):
    """Expected diagnostic failure with a user-facing message."""


def _numpy():
    try:
        return importlib.import_module("numpy")
    except ImportError as exc:
        raise CheckFailure(f"Could not import numpy. {OPTIONAL_HINTS['numpy']}") from exc


def _add_repo_root(repo_root: str | None) -> Path | None:
    if not repo_root:
        return None
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise CheckFailure(f"--repo-root does not exist: {root}")
    if not (root / "pahelix").is_dir():
        raise CheckFailure(f"--repo-root must contain a pahelix package directory: {root}")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return root


def _import_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        missing = getattr(exc, "name", None) or module_name.split(".")[0]
        hint = OPTIONAL_HINTS.get(missing, "Install the missing package or choose a dependency-light check.")
        raise CheckFailure(f"Could not import {module_name}: missing {missing}. {hint}") from exc


def _load_module_from_repo(repo_root: Path, relative_path: str, module_name: str):
    module_path = repo_root / relative_path
    if not module_path.exists():
        raise CheckFailure(f"Expected source file is missing under package root: {relative_path}")
    root_text = str(repo_root)
    added_root = False
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
        added_root = True
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise CheckFailure(f"Could not load source module from: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:
        missing = getattr(exc, "name", None) or relative_path
        hint = OPTIONAL_HINTS.get(missing, "Install the missing package or choose a dependency-light check.")
        raise CheckFailure(f"Could not load {relative_path}: missing {missing}. {hint}") from exc
    finally:
        if added_root:
            try:
                sys.path.remove(root_text)
            except ValueError:
                pass
    return module


def _pahelix_source_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root
    pahelix = _import_module("pahelix")
    package_file = getattr(pahelix, "__file__", None)
    if not package_file:
        raise CheckFailure("Imported pahelix but could not locate its package files")
    return Path(package_file).resolve().parent.parent


def _format_exc(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def check_imports(repo_root: Path | None) -> None:
    _import_module("pahelix")
    source_root = _pahelix_source_root(repo_root)
    _load_module_from_repo(source_root, "pahelix/utils/data_utils.py", "paddlehelix_check_import_data_utils")
    _load_module_from_repo(source_root, "pahelix/utils/protein_tools.py", "paddlehelix_check_import_protein_tools")
    print("ok imports: pahelix, data_utils source, protein_tools source")
    optional_sources = (
        ("pahelix.datasets.inmemory_dataset", "pahelix/datasets/inmemory_dataset.py"),
        ("pahelix.utils.splitters", "pahelix/utils/splitters.py"),
        ("pahelix.utils.compound_tools", "pahelix/utils/compound_tools.py"),
        ("pahelix.model_zoo.pretrain_gnns_model", "pahelix/model_zoo/pretrain_gnns_model.py"),
    )
    for module_name, relative_path in optional_sources:
        try:
            _load_module_from_repo(source_root, relative_path, "paddlehelix_check_optional_" + module_name.replace(".", "_"))
        except CheckFailure as exc:
            print(f"optional import skipped: {module_name}: {exc}")
        else:
            print(f"ok optional import: {module_name}")


class SimpleInMemoryDataset:
    def __init__(self, data_list):
        self.data_list = list(data_list)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return SimpleInMemoryDataset(self.data_list[key])
        if isinstance(key, list):
            return SimpleInMemoryDataset([self.data_list[index] for index in key])
        if hasattr(key, "tolist") and not isinstance(key, (str, bytes)):
            converted = key.tolist()
            if isinstance(converted, list):
                return SimpleInMemoryDataset([self.data_list[int(index)] for index in converted])
        return self.data_list[int(key)]

    def __len__(self):
        return len(self.data_list)


def check_dataset(repo_root: Path | None) -> None:
    np = _numpy()
    source_root = _pahelix_source_root(repo_root)
    data_utils = _load_module_from_repo(source_root, "pahelix/utils/data_utils.py", "paddlehelix_check_data_utils")

    data_list = [
        {"a": np.array([1, 23, 4], dtype="int64"), "label": np.array([1.0], dtype="float32")},
        {"a": np.array([2, 34, 5], dtype="int64"), "label": np.array([0.0], dtype="float32")},
    ]
    with tempfile.TemporaryDirectory(prefix="paddlehelix-core-api-") as tmp_dir:
        npz_file = Path(tmp_dir) / "tiny.npz"
        data_utils.save_data_list_to_npz(data_list, str(npz_file))
        reloaded = data_utils.load_npz_to_data_list(str(npz_file))
    if len(reloaded) != len(data_list):
        raise CheckFailure(f"NPZ reload length mismatch: saved {len(data_list)}, loaded {len(reloaded)}")
    for index, (expected, actual) in enumerate(zip(data_list, reloaded)):
        if set(expected) != set(actual):
            raise CheckFailure(f"NPZ reload key mismatch at record {index}: expected {sorted(expected)}, got {sorted(actual)}")
        for key in expected:
            if not np.array_equal(np.asarray(expected[key]), np.asarray(actual[key])):
                raise CheckFailure(f"NPZ reload value mismatch at record {index}, key {key!r}")
    print("ok dataset: save_data_list_to_npz/load_npz_to_data_list round trip")

    try:
        inmemory = _load_module_from_repo(source_root, "pahelix/datasets/inmemory_dataset.py", "paddlehelix_check_inmemory_dataset")
    except CheckFailure as exc:
        print(f"optional InMemoryDataset import skipped: {exc}")
    else:
        dataset = inmemory.InMemoryDataset(data_list=data_list)
        subset = dataset[[1, 0]]
        if len(dataset) != 2 or len(subset) != 2:
            raise CheckFailure("InMemoryDataset list indexing returned an unexpected length")
        print("ok dataset: InMemoryDataset construction and list indexing")


def check_protein_tokenizer(repo_root: Path | None) -> None:
    source_root = _pahelix_source_root(repo_root)
    protein_tools = _load_module_from_repo(source_root, "pahelix/utils/protein_tools.py", "paddlehelix_check_protein_tools")
    tokenizer = protein_tools.ProteinTokenizer()
    ids = tokenizer.gen_token_ids("ACD?")
    expected = [
        protein_tools.ProteinTokenizer.start_token_id,
        protein_tools.ProteinTokenizer.vocab["A"],
        protein_tools.ProteinTokenizer.vocab["C"],
        protein_tools.ProteinTokenizer.vocab["D"],
        protein_tools.ProteinTokenizer.unknown_token_id,
        protein_tools.ProteinTokenizer.end_token_id,
    ]
    if ids != expected:
        raise CheckFailure(f"Unexpected token IDs for ACD?: got {ids}, expected {expected}")
    print("ok protein-tokenizer: boundary tokens and unknown-token mapping")


def check_rdkit(repo_root: Path | None) -> None:
    try:
        chem = _import_module("rdkit.Chem")
    except CheckFailure as exc:
        raise CheckFailure(f"RDKit is unavailable. {exc}") from exc
    mol = chem.MolFromSmiles("CCO")
    if mol is None:
        raise CheckFailure("RDKit imported but failed to parse a simple CCO SMILES")
    print("ok rdkit: parsed CCO")


def check_splitters(repo_root: Path | None) -> None:
    source_root = _pahelix_source_root(repo_root)
    try:
        splitters = _load_module_from_repo(source_root, "pahelix/utils/splitters.py", "paddlehelix_check_splitters")
    except CheckFailure as exc:
        raise CheckFailure(f"Could not import pahelix.utils.splitters: {exc}") from exc
    dataset = SimpleInMemoryDataset(
        [
            {"smiles": "CCO"},
            {"smiles": "CCN"},
            {"smiles": "c1ccccc1"},
            {"smiles": "CCCl"},
            {"smiles": "CCBr"},
            {"smiles": "CC(=O)O"},
            {"smiles": "CC(C)O"},
            {"smiles": "CCC"},
            {"smiles": "CCS"},
            {"smiles": "CCF"},
        ]
    )
    random_train, random_valid, random_test = splitters.RandomSplitter().split(dataset, 0.6, 0.2, 0.2, seed=7)
    index_train, index_valid, index_test = splitters.IndexSplitter().split(dataset, 0.6, 0.2, 0.2)
    if sum(map(len, (random_train, random_valid, random_test))) != len(dataset):
        raise CheckFailure("RandomSplitter did not preserve the total dataset length")
    if sum(map(len, (index_train, index_valid, index_test))) != len(dataset):
        raise CheckFailure("IndexSplitter did not preserve the total dataset length")
    print("ok splitters: random and index split preserve record count")

    scaffold_train, scaffold_valid, scaffold_test = splitters.ScaffoldSplitter().split(dataset, 0.6, 0.2, 0.2)
    random_scaffold_train, random_scaffold_valid, random_scaffold_test = splitters.RandomScaffoldSplitter().split(dataset, 0.6, 0.2, 0.2, seed=7)
    if sum(map(len, (scaffold_train, scaffold_valid, scaffold_test))) != len(dataset):
        raise CheckFailure("ScaffoldSplitter did not preserve the total dataset length")
    if sum(map(len, (random_scaffold_train, random_scaffold_valid, random_scaffold_test))) != len(dataset):
        raise CheckFailure("RandomScaffoldSplitter did not preserve the total dataset length")
    print("ok splitters: scaffold and random-scaffold split preserve record count")


def simulate_npz_mismatch(repo_root: Path | None) -> None:
    np = _numpy()
    source_root = _pahelix_source_root(repo_root)
    data_utils = _load_module_from_repo(source_root, "pahelix/utils/data_utils.py", "paddlehelix_check_data_utils_mismatch")
    with tempfile.TemporaryDirectory(prefix="paddlehelix-core-api-bad-") as tmp_dir:
        bad_file = Path(tmp_dir) / "bad.npz"
        np.savez_compressed(str(bad_file), a=np.array([1, 2, 3]), **{"a.seq_len": np.array([1, 2])})
        try:
            data_utils.load_npz_to_data_list(str(bad_file))
        except Exception as exc:  # noqa: BLE001 - this is an intentional diagnostic demonstration.
            print("ok simulate-npz-mismatch: cache is missing required metadata or has inconsistent keys")
            print(f"diagnosis: { _format_exc(exc) }")
            return
    raise CheckFailure("Simulated NPZ mismatch unexpectedly loaded without an error")


def simulate_missing_smiles(repo_root: Path | None) -> None:
    try:
        source_root = _pahelix_source_root(repo_root)
        splitters = _load_module_from_repo(source_root, "pahelix/utils/splitters.py", "paddlehelix_check_splitters_missing_smiles")
    except (CheckFailure, ImportError) as exc:
        print(f"ok simulate-missing-smiles: scaffold split cannot run before optional dependencies import cleanly: {exc}")
        return
    dataset = SimpleInMemoryDataset([{"name": "record-without-smiles"}, {"smiles": "CCO"}])
    try:
        splitters.ScaffoldSplitter().split(dataset, 0.5, 0.25, 0.25)
    except KeyError as exc:
        print("ok simulate-missing-smiles: scaffold split requires every record to contain 'smiles'")
        print(f"diagnosis: { _format_exc(exc) }")
        return
    except Exception as exc:  # noqa: BLE001 - report unexpected shape as a diagnostic.
        print("ok simulate-missing-smiles: scaffold split failed before completion")
        print(f"diagnosis: { _format_exc(exc) }")
        return
    raise CheckFailure("Simulated missing-smiles scaffold split unexpectedly succeeded")


CHECKS: dict[str, Callable[[Path | None], None]] = {
    "imports": check_imports,
    "dataset": check_dataset,
    "protein-tokenizer": check_protein_tokenizer,
    "rdkit": check_rdkit,
    "splitters": check_splitters,
}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe, tiny diagnostics for core PaddleHelix pahelix APIs.",
    )
    parser.add_argument(
        "--repo-root",
        help="Optional PaddleHelix source checkout. Added to sys.path only when provided.",
    )
    parser.add_argument(
        "--check",
        action="append",
        choices=sorted(CHECKS),
        help="Check to run. May be repeated. Defaults to imports and protein-tokenizer.",
    )
    parser.add_argument(
        "--simulate-npz-mismatch",
        action="store_true",
        help="Create an intentionally malformed temporary NPZ and show the expected data-format diagnosis.",
    )
    parser.add_argument(
        "--simulate-missing-smiles",
        action="store_true",
        help="Show the expected diagnosis for scaffold splitting records that lack a smiles key.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repo_root = _add_repo_root(args.repo_root)
        has_simulation = args.simulate_npz_mismatch or args.simulate_missing_smiles
        selected_checks = args.check or ([] if has_simulation else ["imports", "protein-tokenizer"])
        for check_name in selected_checks:
            CHECKS[check_name](repo_root)
        if args.simulate_npz_mismatch:
            simulate_npz_mismatch(repo_root)
        if args.simulate_missing_smiles:
            simulate_missing_smiles(repo_root)
    except CheckFailure as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - convert unexpected exceptions to concise diagnostics.
        print(f"FAILED: unexpected { _format_exc(exc) }", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
