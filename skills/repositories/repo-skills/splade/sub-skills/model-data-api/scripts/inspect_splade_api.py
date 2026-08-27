#!/usr/bin/env python3
"""Inspect installed SPLADE API signatures without downloading model weights."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import asdict, dataclass, field
from importlib import metadata
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class SymbolReport:
    module: str
    name: str
    ok: bool
    signature: Optional[str] = None
    kind: Optional[str] = None
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleReport:
    module: str
    ok: bool
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Report:
    ok: bool
    versions: Dict[str, Optional[str]] = field(default_factory=dict)
    modules: List[ModuleReport] = field(default_factory=list)
    symbols: List[SymbolReport] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "versions": self.versions,
            "modules": [item.as_dict() for item in self.modules],
            "symbols": [item.as_dict() for item in self.symbols],
        }


SYMBOLS = [
    ("splade.models.transformer_rep", "TransformerRep"),
    ("splade.models.transformer_rep", "SiameseBase"),
    ("splade.models.transformer_rep", "Splade"),
    ("splade.models.transformer_rep", "SpladeDoc"),
    ("splade.models.transformer_rep", "SpladeTopK"),
    ("splade.models.transformer_rep", "SpladeLexical"),
    ("splade.models.transformer_rank", "TransformerRank"),
    ("splade.models.transformer_rank", "RankT5Encoder"),
    ("splade.models.models_utils", "get_model"),
    ("splade.hf.models", "SPLADE"),
    ("splade.hf.models", "DPR"),
    ("splade.hf.models", "SpladeDoc"),
    ("splade.hf.args", "ModelArguments"),
    ("splade.hf.args", "DataTrainingArguments"),
    ("splade.hf.args", "LocalTrainingArguments"),
    ("splade.datasets.datasets", "CollectionDatasetPreLoad"),
    ("splade.datasets.datasets", "PairsDatasetPreLoad"),
    ("splade.datasets.datasets", "DistilPairsDatasetPreLoad"),
    ("splade.datasets.datasets", "MsMarcoHardNegatives"),
    ("splade.hf.datasets", "DatasetPreLoad"),
    ("splade.hf.datasets", "L2I_Dataset"),
    ("splade.hf.datasets", "RerankingDataset"),
    ("splade.hf.datasets", "TRIPLET_Dataset"),
    ("splade.datasets.rerank", "EvalDatasetRerank"),
    ("splade.datasets.rerank", "EvalDatasetMonoT5"),
    ("splade.datasets.rerank", "EvalDatasetRerankPairwise"),
    ("splade.datasets.dataloaders", "SiamesePairsDataLoader"),
    ("splade.datasets.dataloaders", "CollectionDataLoader"),
    ("splade.datasets.dataloaders", "EvalDataLoader"),
    ("splade.indexing.inverted_index", "IndexDictOfArray"),
    ("splade.tasks.transformer_evaluator", "SparseIndexing"),
    ("splade.tasks.transformer_evaluator", "SparseRetrieval"),
    ("splade.tasks.transformer_evaluator", "EncodeAnserini"),
    ("splade.utils.utils", "get_loss"),
    ("splade.utils.utils", "generate_bow"),
    ("splade.utils.utils", "clean_bow"),
    ("splade.utils.utils", "pruning"),
    ("splade.utils.utils", "normalize"),
]

VERSION_PACKAGES = ["splade", "torch", "transformers", "omegaconf", "hydra-core", "h5py", "numba"]


def package_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001 - diagnostic script should continue.
        return f"error: {exc}"


def signature_for(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        if inspect.isclass(obj) and hasattr(obj, "__init__"):
            return str(inspect.signature(obj.__init__))
        raise


def inspect_api(symbol_filter: Optional[Sequence[str]] = None) -> Report:
    wanted = set(symbol_filter or [])
    modules: Dict[str, ModuleReport] = {}
    symbols: List[SymbolReport] = []
    imported: Dict[str, Any] = {}

    for module_name, symbol_name in SYMBOLS:
        full_name = f"{module_name}.{symbol_name}"
        if wanted and symbol_name not in wanted and full_name not in wanted and module_name not in wanted:
            continue
        if module_name not in imported:
            try:
                imported[module_name] = importlib.import_module(module_name)
                modules[module_name] = ModuleReport(module=module_name, ok=True)
            except Exception as exc:  # noqa: BLE001 - keep collecting diagnostics.
                modules[module_name] = ModuleReport(module=module_name, ok=False, error=f"{type(exc).__name__}: {exc}")
                imported[module_name] = None
        module = imported[module_name]
        if module is None:
            symbols.append(
                SymbolReport(
                    module=module_name,
                    name=symbol_name,
                    ok=False,
                    error=f"module import failed: {modules[module_name].error}",
                )
            )
            continue
        try:
            obj = getattr(module, symbol_name)
            kind = "class" if inspect.isclass(obj) else "function" if inspect.isfunction(obj) else type(obj).__name__
            symbols.append(
                SymbolReport(
                    module=module_name,
                    name=symbol_name,
                    ok=True,
                    kind=kind,
                    signature=signature_for(obj),
                )
            )
        except Exception as exc:  # noqa: BLE001 - keep collecting diagnostics.
            symbols.append(
                SymbolReport(
                    module=module_name,
                    name=symbol_name,
                    ok=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    ok = all(item.ok for item in modules.values()) and all(item.ok for item in symbols)
    return Report(
        ok=ok,
        versions={package: package_version(package) for package in VERSION_PACKAGES},
        modules=list(modules.values()),
        symbols=symbols,
    )


def print_text(report: Report) -> None:
    print("Versions:")
    for name, version in report.versions.items():
        print(f"  {name}: {version or 'not installed'}")
    print("Modules:")
    for module in report.modules:
        status = "OK" if module.ok else "FAIL"
        print(f"  [{status}] {module.module}")
        if module.error:
            print(f"    {module.error}")
    print("Symbols:")
    for symbol in report.symbols:
        status = "OK" if symbol.ok else "FAIL"
        print(f"  [{status}] {symbol.module}.{symbol.name}")
        if symbol.signature:
            print(f"    {symbol.signature}")
        if symbol.error:
            print(f"    {symbol.error}")
    print(f"Overall: {'OK' if report.ok else 'FAIL'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect installed SPLADE API signatures without model downloads.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--symbol",
        action="append",
        help="Restrict output to a symbol, module, or fully qualified module.symbol. May be repeated.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = inspect_api(args.symbol)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
