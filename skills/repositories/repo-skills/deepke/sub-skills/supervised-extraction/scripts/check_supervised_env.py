#!/usr/bin/env python3
"""Safe DeepKE supervised-extraction runtime diagnostic.

This script checks imports, Python/package versions, CUDA visibility, and optional
user-provided data/checkpoint paths. It never starts training, never performs
model inference, and never downloads remote assets.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Dict, Iterable, List, Tuple

ImportSpec = Tuple[str, str]
DataExpectation = Tuple[str, List[str], bool]

COMMON_IMPORTS: List[ImportSpec] = [
    ("deepke", "deepke"),
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("hydra", "hydra-core"),
    ("omegaconf", "omegaconf"),
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("seqeval", "seqeval"),
    ("jieba", "jieba"),
    ("ujson", "ujson"),
    ("pyhocon", "pyhocon"),
    ("tqdm", "tqdm"),
    ("nltk", "nltk"),
]

TASKS: Dict[str, Dict[str, Any]] = {
    "ner-standard": {
        "modules": ["deepke.name_entity_re.standard"],
        "data": [
            ("training BIO file", ["train.txt"], True),
            ("validation BIO file", ["valid.txt", "dev.txt"], True),
            ("test BIO file", ["test.txt"], True),
        ],
        "checkpoint_note": "BERT/W2NER checkpoint directory or BiLSTM-CRF checkpoint plus matching vocabulary file.",
        "pretrained_note": "BERT model name or local transformer directory when using the bert model selector.",
    },
    "ner-few-shot": {
        "modules": ["deepke.name_entity_re.few_shot"],
        "data": [
            ("CoNLL-style train file or k-shot train file", ["train.txt", "k-shot-train.txt", "10-shot-train.txt", "20-shot-train.txt", "50-shot-train.txt", "100-shot-train.txt", "200-shot-train.txt", "500-shot-train.txt"], True),
            ("validation file when available", ["valid.txt", "val.txt"], False),
            ("test file", ["test.txt"], True),
        ],
        "checkpoint_note": "Prediction requires a non-empty load_path pointing to a tuned few-shot model/prompt artifact.",
        "pretrained_note": "BART or Chinese-BART compatible model name/local directory.",
    },
    "ner-cross": {
        "modules": ["deepke.name_entity_re.cross"],
        "data": [
            ("domain train JSON", ["train.json"], True),
            ("domain validation JSON", ["val.json", "valid.json"], True),
            ("domain test JSON", ["test.json"], True),
            ("record schema", ["record.schema"], True),
            ("entity/event/relation schema files", ["entity.schema", "event.schema", "relation.schema"], False),
        ],
        "checkpoint_note": "Transfer requires source_prefix_path/target_prefix_path/multi_source_path artifacts.",
        "pretrained_note": "T5/generative PLM path or tuned target-domain model path.",
    },
    "ner-multimodal": {
        "modules": ["deepke.name_entity_re.multimodal"],
        "data": [
            ("text train split", ["train.txt"], True),
            ("text validation split", ["valid.txt", "dev.txt"], False),
            ("text test split", ["test.txt"], True),
            ("detected object directory", ["twitter15_detect", "twitter17_detect", "detect", "img_detect"], True),
            ("visual grounding directory", ["twitter2015_aux_images", "twitter2017_aux_images", "aux_images", "img_vg"], True),
            ("original image directory", ["twitter2015_images", "twitter2017_images", "images", "img_org"], True),
        ],
        "checkpoint_note": "Prediction requires load_path pointing to a trained multimodal checkpoint.",
        "pretrained_note": "BERT text model plus CLIP/Vision Transformer directory for vit_name.",
    },
    "re-standard": {
        "modules": ["deepke.relation_extraction.standard"],
        "data": [
            ("train CSV", ["train.csv", "origin/train.csv"], True),
            ("validation CSV", ["valid.csv", "origin/valid.csv", "dev.csv", "origin/dev.csv"], True),
            ("test CSV", ["test.csv", "origin/test.csv"], True),
            ("relation inventory", ["relation.csv", "origin/relation.csv"], True),
        ],
        "checkpoint_note": "Prediction requires predict.fp pointing to a trained .pth checkpoint that matches the selected model family.",
        "pretrained_note": "For model=lm, lm_file should be a resolvable local path or model name.",
    },
    "re-few-shot": {
        "modules": ["deepke.relation_extraction.few_shot"],
        "data": [
            ("relation id map", ["rel2id.json"], True),
            ("train split", ["train.txt"], True),
            ("validation split", ["val.txt", "valid.txt"], True),
            ("test split", ["test.txt"], True),
        ],
        "checkpoint_note": "save_path/load_path or train_from_saved_model should point to the intended prompt model artifact.",
        "pretrained_note": "BERT masked-LM model name or local directory.",
    },
    "re-document": {
        "modules": ["deepke.relation_extraction.document"],
        "data": [
            ("dev JSON", ["dev.json"], True),
            ("test JSON", ["test.json"], True),
            ("relation info JSON", ["rel_info.json"], True),
            ("relation id JSON", ["rel2id.json"], True),
            ("manual or distant train JSON", ["train_annotated.json", "train_distant.json"], True),
        ],
        "checkpoint_note": "load_path/save_path should point to the DocuNet-style .pt model artifact.",
        "pretrained_note": "RoBERTa/BERT model name or local directory matching transformer_type.",
    },
    "re-multimodal": {
        "modules": ["deepke.relation_extraction.multimodal"],
        "data": [
            ("text folder", ["txt"], True),
            ("relation id JSON", ["ours_rel2id.json", "rel2id.json"], True),
            ("detected object directory", ["img_detect", "detect"], True),
            ("visual grounding directory", ["img_vg", "vg_data"], True),
            ("original image directory", ["img_org", "images"], True),
        ],
        "checkpoint_note": "Prediction requires load_path pointing to a trained multimodal RE checkpoint.",
        "pretrained_note": "BERT text model plus CLIP/Vision Transformer directory for vit_name.",
    },
    "ae-standard": {
        "modules": ["deepke.attribution_extraction.standard"],
        "data": [
            ("train CSV", ["train.csv", "origin/train.csv"], True),
            ("validation CSV", ["valid.csv", "origin/valid.csv", "dev.csv", "origin/dev.csv"], True),
            ("test CSV", ["test.csv", "origin/test.csv"], True),
            ("attribute inventory", ["attribute.csv", "origin/attribute.csv"], True),
        ],
        "checkpoint_note": "Prediction requires predict.fp pointing to a trained .pth checkpoint that matches the selected model family.",
        "pretrained_note": "For model=lm, lm_file should be a resolvable local path or model name.",
    },
    "ee-standard": {
        "modules": ["deepke.event_extraction.standard"],
        "data": [
            ("trigger data directory", ["trigger", "ACE/trigger", "DuEE/trigger"], True),
            ("role data directory", ["role", "ACE/role", "DuEE/role"], True),
            ("schema/tag directory", ["schema", "ACE/schema", "DuEE/schema"], True),
            ("trigger prediction JSON for role pipeline", ["eval_pred.json", "trigger/eval_pred.json", "exp/trigger/eval_pred.json"], False),
        ],
        "checkpoint_note": "Role prediction requires a trained role model path and trigger prediction JSON files.",
        "pretrained_note": "BERT model path/name; use an English model for ACE and Chinese model for DuEE.",
    },
    "cnschema-ner": {
        "modules": ["deepke.name_entity_re.standard"],
        "data": [],
        "checkpoint_note": "Off-the-shelf NER model directory should contain transformer/tokenizer files or a supported NER checkpoint layout.",
        "pretrained_note": "Chinese BERT/RoBERTa model assets may be bundled inside the checkpoint directory or supplied separately.",
    },
    "cnschema-re": {
        "modules": ["deepke.relation_extraction.standard"],
        "data": [
            ("relation inventory", ["relation.csv", "origin/relation.csv"], False),
        ],
        "checkpoint_note": "Off-the-shelf RE checkpoint is normally a .pth file used by predict.fp; num_relations should match the cnSchema inventory.",
        "pretrained_note": "Chinese BERT/RoBERTa LM asset for lm_file if the checkpoint/config expects one.",
    },
}


def version_for(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def check_import(module: str, dist: str | None = None) -> Dict[str, Any]:
    record: Dict[str, Any] = {"module": module, "ok": False, "version": None, "error": None}
    try:
        importlib.import_module(module)
        record["ok"] = True
    except Exception as exc:  # noqa: BLE001 - diagnostic should capture any import error
        record["error"] = f"{exc.__class__.__name__}: {exc}"
    if dist:
        record["version"] = version_for(dist)
    return record


def check_torchcrf() -> Dict[str, Any]:
    for module in ("torchcrf", "TorchCRF"):
        rec = check_import(module, "pytorch-crf")
        if rec["ok"]:
            rec["module"] = "torchcrf or TorchCRF"
            return rec
    rec = check_import("torchcrf", "pytorch-crf")
    rec["module"] = "torchcrf or TorchCRF"
    return rec


def cuda_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {"torch_imported": False, "available": False, "device_count": 0, "torch_version": None, "error": None}
    try:
        import torch  # type: ignore

        info["torch_imported"] = True
        info["torch_version"] = getattr(torch, "__version__", None)
        info["available"] = bool(torch.cuda.is_available())
        info["device_count"] = int(torch.cuda.device_count())
        if info["available"]:
            info["devices"] = [torch.cuda.get_device_name(i) for i in range(info["device_count"])]
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{exc.__class__.__name__}: {exc}"
    return info


def path_record(path_text: str, kind: str) -> Dict[str, Any]:
    path = Path(path_text).expanduser()
    rec: Dict[str, Any] = {"kind": kind, "path": path_text, "exists": path.exists()}
    if path.exists():
        rec["is_file"] = path.is_file()
        rec["is_dir"] = path.is_dir()
    return rec


def check_data_dir(data_dir: str, expectations: Iterable[DataExpectation]) -> List[Dict[str, Any]]:
    root = Path(data_dir).expanduser()
    results: List[Dict[str, Any]] = []
    for label, candidates, required in expectations:
        found = []
        for candidate in candidates:
            candidate_path = root / candidate
            if candidate_path.exists():
                found.append(candidate)
        results.append(
            {
                "label": label,
                "required": required,
                "ok": bool(found),
                "found": found,
                "candidates": candidates,
            }
        )
    return results


def cnschema_checkpoint_hint(checkpoint: str | None) -> Dict[str, Any] | None:
    if not checkpoint:
        return None
    path = Path(checkpoint).expanduser()
    if not path.is_dir():
        return None
    expected_any = ["pytorch_model.bin", "model.safetensors", "config.json", "vocab.txt", "tokenizer_config.json", "special_tokens_map.json"]
    found = [name for name in expected_any if (path / name).exists()]
    return {
        "checkpoint_path": checkpoint,
        "looks_like_transformer_dir": bool({"config.json", "vocab.txt"}.intersection(found) and {"pytorch_model.bin", "model.safetensors"}.intersection(found)),
        "found_common_files": found,
        "expected_common_files": expected_any,
    }


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    selected_tasks = list(TASKS) if args.task == "all" else [args.task]
    task_modules = sorted({module for task in selected_tasks for module in TASKS[task]["modules"]})

    import_results = [check_import(module, dist) for module, dist in COMMON_IMPORTS]
    import_results.append(check_torchcrf())
    task_import_results = [check_import(module, "deepke") for module in task_modules]

    report: Dict[str, Any] = {
        "script": "check_supervised_env.py",
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "environment": {
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        },
        "selected_tasks": selected_tasks,
        "imports": import_results,
        "task_imports": task_import_results,
        "cuda": cuda_info(),
        "paths": {},
        "notes": [],
    }

    if args.data_dir:
        per_task = {}
        for task in selected_tasks:
            per_task[task] = check_data_dir(args.data_dir, TASKS[task].get("data", []))
        report["paths"]["data_dir"] = path_record(args.data_dir, "data_dir")
        report["paths"]["data_expectations"] = per_task
    else:
        report["notes"].append("No --data-dir supplied; data layout was not checked.")

    if args.checkpoint:
        report["paths"]["checkpoint"] = path_record(args.checkpoint, "checkpoint")
        hint = cnschema_checkpoint_hint(args.checkpoint)
        if hint:
            report["paths"]["checkpoint_transformer_hint"] = hint
    else:
        report["notes"].append("No --checkpoint supplied; checkpoint/model artifact existence was not checked.")

    if args.pretrained_model:
        p = Path(args.pretrained_model).expanduser()
        if p.exists() or any(sep in args.pretrained_model for sep in ("/", "\\")) or args.pretrained_model.startswith("."):
            report["paths"]["pretrained_model"] = path_record(args.pretrained_model, "pretrained_model")
        else:
            report["paths"]["pretrained_model"] = {
                "kind": "pretrained_model",
                "value": args.pretrained_model,
                "exists": None,
                "note": "Value does not look like a local path; it may be a remote model id and could trigger downloads in native DeepKE code.",
            }
    else:
        report["notes"].append("No --pretrained-model supplied; local PLM/CLIP assets were not checked.")

    if args.require_cuda and not report["cuda"].get("available"):
        report["notes"].append("--require-cuda was set but torch.cuda.is_available() is false.")

    report["task_expectations"] = {
        task: {
            "checkpoint_note": TASKS[task].get("checkpoint_note"),
            "pretrained_note": TASKS[task].get("pretrained_note"),
        }
        for task in selected_tasks
    }
    return report


def has_failures(report: Dict[str, Any], args: argparse.Namespace) -> bool:
    failures = []
    failures.extend(not item.get("ok") for item in report.get("imports", []) if item.get("module") in {"deepke", "torch"})
    failures.extend(not item.get("ok") for item in report.get("task_imports", []))
    if args.require_cuda and not report.get("cuda", {}).get("available"):
        failures.append(True)
    if args.data_dir:
        for task_results in report.get("paths", {}).get("data_expectations", {}).values():
            for item in task_results:
                if item.get("required") and not item.get("ok"):
                    failures.append(True)
    if args.checkpoint and not report.get("paths", {}).get("checkpoint", {}).get("exists"):
        failures.append(True)
    if args.pretrained_model:
        rec = report.get("paths", {}).get("pretrained_model", {})
        if rec.get("exists") is False:
            failures.append(True)
    return any(failures)


def print_text(report: Dict[str, Any]) -> None:
    print("DeepKE supervised extraction diagnostic")
    print(f"Python: {report['python']['version']} ({report['python']['platform']})")
    print(f"Executable: {report['python']['executable']}")
    print("\nCore imports:")
    for item in report["imports"]:
        status = "OK" if item["ok"] else "MISSING"
        version = f" version={item['version']}" if item.get("version") else ""
        error = f" error={item['error']}" if item.get("error") else ""
        print(f"  [{status}] {item['module']}{version}{error}")
    print("\nTask imports:")
    for item in report["task_imports"]:
        status = "OK" if item["ok"] else "MISSING"
        error = f" error={item['error']}" if item.get("error") else ""
        print(f"  [{status}] {item['module']}{error}")
    cuda = report["cuda"]
    print("\nCUDA:")
    print(f"  torch_imported={cuda.get('torch_imported')} available={cuda.get('available')} device_count={cuda.get('device_count')} torch_version={cuda.get('torch_version')}")
    if cuda.get("devices"):
        for i, name in enumerate(cuda["devices"]):
            print(f"  device[{i}]={name}")
    if cuda.get("error"):
        print(f"  error={cuda['error']}")
    paths = report.get("paths", {})
    if paths:
        print("\nPath checks:")
        for key in ("data_dir", "checkpoint", "pretrained_model"):
            if key in paths:
                print(f"  {key}: {paths[key]}")
        if "checkpoint_transformer_hint" in paths:
            print(f"  checkpoint_transformer_hint: {paths['checkpoint_transformer_hint']}")
        if "data_expectations" in paths:
            print("\nData expectations:")
            for task, items in paths["data_expectations"].items():
                print(f"  {task}:")
                if not items:
                    print("    (no data-dir expectations for this task)")
                for item in items:
                    status = "OK" if item["ok"] else ("MISSING" if item["required"] else "not found/optional")
                    print(f"    [{status}] {item['label']} candidates={item['candidates']} found={item['found']}")
    print("\nTask notes:")
    for task, notes in report.get("task_expectations", {}).items():
        print(f"  {task}:")
        print(f"    checkpoint: {notes.get('checkpoint_note')}")
        print(f"    pretrained: {notes.get('pretrained_note')}")
    if report.get("notes"):
        print("\nGeneral notes:")
        for note in report["notes"]:
            print(f"  - {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely check a DeepKE supervised extraction environment without training or downloading.")
    parser.add_argument("--task", choices=["all", *sorted(TASKS)], default="all", help="Task/scenario expectations to check.")
    parser.add_argument("--data-dir", help="Optional dataset directory to check against the selected task's expected files.")
    parser.add_argument("--checkpoint", help="Optional checkpoint/model path to check for existence.")
    parser.add_argument("--pretrained-model", help="Optional pretrained model path or id to report; local paths are checked for existence.")
    parser.add_argument("--require-cuda", action="store_true", help="Mark CUDA absence as a strict failure.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required imports, paths, data expectations, or CUDA checks fail.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if args.strict and has_failures(report, args) else 0


if __name__ == "__main__":
    raise SystemExit(main())
