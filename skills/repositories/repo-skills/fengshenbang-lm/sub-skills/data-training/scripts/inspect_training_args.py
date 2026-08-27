#!/usr/bin/env python3
"""Print grouped argparse destinations for available Fengshen training providers.

This script is safe:
- it uses lazy imports,
- it does not download models or datasets,
- it only constructs parsers and prints their argument destinations.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence


@dataclass(frozen=True)
class Provider:
    category: str
    label: str
    loader: Callable[[], Callable[[argparse.ArgumentParser], Any]]


def _load_attr(module_name: str, attr_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def _ensure_legacy_module_aliases() -> None:
    """Patch legacy import paths used by the repo so introspection stays checkout-independent."""

    if "fengshen.data.mmap_index_dataset" not in sys.modules:
        sys.modules["fengshen.data.mmap_index_dataset"] = importlib.import_module(
            "fengshen.data.mmap_dataloader.mmap_index_dataset"
        )


def _provider_registry() -> list[Provider]:
    _ensure_legacy_module_aliases()
    return [
        Provider(
            category="module",
            label="model_utils.add_module_args",
            loader=lambda: _load_attr("fengshen.models.model_utils", "add_module_args"),
        ),
        Provider(
            category="module",
            label="model_utils.add_inverse_square_args",
            loader=lambda: _load_attr("fengshen.models.model_utils", "add_inverse_square_args"),
        ),
        Provider(
            category="data",
            label="UniversalDataModule.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.universal_datamodule.universal_datamodule",
                "UniversalDataModule",
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="MMapDataModule.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.mmap_dataloader.mmap_datamodule", "MMapDataModule"
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="BertDataModule.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.bert_dataloader.load", "BertDataModule"
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="LCSTSDataModel.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.task_dataloader.task_datasets", "LCSTSDataModel"
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="GPT2QADataModel.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.task_dataloader.medicalQADataset", "GPT2QADataModel"
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="UnsuperviseT5DataModel.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.t5_dataloader.t5_datasets", "UnsuperviseT5DataModel"
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="TaskT5DataModel.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.t5_dataloader.t5_datasets", "TaskT5DataModel"
            ).add_data_specific_args,
        ),
        Provider(
            category="data",
            label="DialogDataModel.add_data_specific_args",
            loader=lambda: _load_attr(
                "fengshen.data.t5_dataloader.t5_gen_datasets", "DialogDataModel"
            ).add_data_specific_args,
        ),
        Provider(
            category="checkpoint",
            label="UniversalCheckpoint.add_argparse_args",
            loader=lambda: _load_attr(
                "fengshen.utils.universal_checkpoint", "UniversalCheckpoint"
            ).add_argparse_args,
        ),
        Provider(
            category="trainer",
            label="pytorch_lightning.Trainer.add_argparse_args",
            loader=lambda: _load_attr("pytorch_lightning", "Trainer").add_argparse_args,
        ),
    ]


def inspect_provider(provider: Provider) -> dict[str, Any]:
    try:
        add_args = provider.loader()
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        return {
            "category": provider.category,
            "label": provider.label,
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    parser = argparse.ArgumentParser(prog=provider.label, add_help=False, allow_abbrev=False)
    try:
        result = add_args(parser)
        if result is not None:
            parser = result
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        return {
            "category": provider.category,
            "label": provider.label,
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    groups: list[dict[str, Any]] = []
    for group in parser._action_groups:
        dests = sorted(
            {
                action.dest
                for action in group._group_actions
                if action.dest != "help"
            }
        )
        if dests:
            groups.append({"title": group.title, "dests": dests})

    all_dests = sorted({dest for group in groups for dest in group["dests"]})
    return {
        "category": provider.category,
        "label": provider.label,
        "available": True,
        "group_count": len(groups),
        "dests": all_dests,
        "groups": groups,
    }


def render_text(items: Sequence[dict[str, Any]]) -> str:
    lines: list[str] = []
    current_category = None
    for item in items:
        if item["category"] != current_category:
            current_category = item["category"]
            lines.append(f"[{current_category}]")
        lines.append(f"- {item['label']}")
        if not item.get("available", False):
            lines.append(f"  unavailable: {item.get('error', 'unknown error')}")
            continue
        for group in item["groups"]:
            dests = ", ".join(group["dests"])
            lines.append(f"  {group['title']}: {dests}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print grouped argparse destinations for Fengshen training providers.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    args = parser.parse_args(argv)

    items = [inspect_provider(provider) for provider in _provider_registry()]
    if args.format == "json":
        print(json.dumps(items, indent=2, ensure_ascii=False))
    else:
        print(render_text(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
