#!/usr/bin/env python3
"""Safe preflight for Baichuan-7B C-Eval and MMLU workflows.

This helper validates local files/options and renders native benchmark commands.
It intentionally does not fetch datasets, import arbitrary benchmark code, load
model weights, or run C-Eval/MMLU inference.
"""

from __future__ import annotations

import argparse
import ast
import csv
import importlib
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

CHOICES = {"A", "B", "C", "D"}
CEVAL_SPLITS = {"dev", "val", "test"}
CEVAL_TASK_COUNT = 52


def q(value: object) -> str:
    return shlex.quote(str(value))


class Report:
    def __init__(self, strict: bool = False) -> None:
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.commands: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    def command(self, command: str) -> None:
        self.commands.append(command)

    @property
    def ok(self) -> bool:
        return not self.errors and not (self.strict and self.warnings)

    def exit_code(self) -> int:
        if self.errors:
            return 1
        if self.strict and self.warnings:
            return 2
        return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "commands": self.commands,
        }

    def print_text(self) -> None:
        status = "OK" if self.ok else "CHECK_FAILED"
        print(f"STATUS: {status}")
        for label, items in (
            ("ERROR", self.errors),
            ("WARNING", self.warnings),
            ("INFO", self.info),
        ):
            for item in items:
                print(f"{label}: {item}")
        if self.commands:
            print("COMMANDS:")
            for command in self.commands:
                print(command)


def resolve_relative(base: Path, maybe_path: str) -> Path:
    p = Path(maybe_path).expanduser()
    return p if p.is_absolute() else (base / p)


def validate_repo_script(repo_root: Optional[str], script_rel: str, report: Report) -> Optional[Path]:
    if not repo_root:
        report.warn(
            f"--repo-root was not provided; cannot verify {script_rel}. Rendered commands will use a placeholder repo path."
        )
        return None
    root = Path(repo_root).expanduser().resolve()
    script = root / script_rel
    if not root.exists():
        report.error(f"repo root does not exist: {root}")
        return script
    if not script.exists():
        report.error(f"native evaluation script is missing: {script}")
    elif not script.is_file():
        report.error(f"native evaluation script path is not a file: {script}")
    else:
        report.note(f"found native evaluation script: {script}")
    return script


def looks_like_remote_id(model: str) -> bool:
    if model.startswith((".", "~", "/")):
        return False
    if os.sep in model or "/" in model:
        return True
    return bool(model and not Path(model).expanduser().exists())


def validate_model_arg(model: str, allow_hf_id: bool, report: Report) -> None:
    model_path = Path(model).expanduser()
    if model_path.exists():
        if not model_path.is_dir():
            report.warn(f"model path exists but is not a directory; Transformers may reject it: {model_path}")
            return
        config = model_path / "config.json"
        if not config.exists():
            report.warn(f"local model directory has no config.json: {model_path}")
        tokenizer_candidates = [
            "tokenizer.model",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
        ]
        if not any((model_path / name).exists() for name in tokenizer_candidates):
            report.warn(
                "local model directory has no obvious tokenizer artifact "
                f"({', '.join(tokenizer_candidates)}): {model_path}"
            )
        weight_patterns = [
            "pytorch_model*.bin",
            "model*.safetensors",
            "*.safetensors",
            "*.bin",
            "pytorch_model.bin.index.json",
            "model.safetensors.index.json",
        ]
        if not any(list(model_path.glob(pattern)) for pattern in weight_patterns):
            report.warn(f"local model directory has no obvious weight shards: {model_path}")
        if config.exists():
            try:
                data = json.loads(config.read_text(encoding="utf-8"))
                if "auto_map" not in data and not any(
                    (model_path / name).exists()
                    for name in ("modeling_baichuan.py", "configuration_baichuan.py", "tokenization_baichuan.py")
                ):
                    report.warn(
                        "config.json has no auto_map and local custom-code files were not obvious; "
                        "Baichuan loading may rely on an external cache or fail despite trust_remote_code=True."
                    )
            except Exception as exc:  # pragma: no cover - defensive diagnostic
                report.warn(f"could not parse config.json for custom-code hints: {exc}")
        report.note(f"validated local model directory shape: {model_path}")
    else:
        if allow_hf_id and looks_like_remote_id(model):
            report.warn(
                f"model argument does not resolve locally and will be treated as a model id/cache lookup at runtime: {model}"
            )
        else:
            report.error(f"model path does not exist: {model}")


def check_imports(packages: Sequence[str], report: Report) -> None:
    for package in packages:
        try:
            mod = importlib.import_module(package)
            version = getattr(mod, "__version__", "unknown")
            report.note(f"import ok: {package} ({version})")
        except Exception as exc:
            report.error(f"cannot import {package}: {exc}")


def check_cuda(report: Report) -> None:
    try:
        import torch  # type: ignore
    except Exception as exc:
        report.error(f"cannot import torch for CUDA check: {exc}")
        return
    try:
        if not torch.cuda.is_available():
            report.error("torch.cuda.is_available() is False; native evaluation scripts call .cuda().")
            return
        device_name = torch.cuda.get_device_name(0)
        tensor = torch.empty((1,), device="cuda")
        del tensor
        report.note(f"CUDA availability/allocation ok on device 0: {device_name}")
    except Exception as exc:
        report.error(f"CUDA allocation check failed: {exc}")


def render_repo_path(repo_root: Optional[str]) -> str:
    return str(Path(repo_root).expanduser().resolve()) if repo_root else "/path/to/Baichuan-7B"


def ceval(args: argparse.Namespace) -> Report:
    report = Report(strict=args.strict)
    validate_repo_script(args.repo_root, "evaluation/evaluate_zh.py", report)
    validate_model_arg(args.model, args.allow_hf_id, report)

    if args.shot < 0:
        report.error("--shot must be non-negative")
    if args.split not in CEVAL_SPLITS:
        report.warn(
            f"--split {args.split!r} is not one of the known C-Eval split names {sorted(CEVAL_SPLITS)}; "
            "evaluate_zh.py will fail with KeyError if the dataset lacks it."
        )
    if args.split == "test":
        report.warn(
            "C-Eval test splits are often unlabeled; evaluate_zh.py requires data['answer'] to compute accuracy. "
            "Use --split val unless you know the selected split is labeled."
        )
    if args.hf_dataset != "ceval/ceval-exam":
        report.warn(
            "evaluate_zh.py hard-codes CEval.DATA_PATH = 'ceval/ceval-exam'. "
            f"The requested dataset label {args.hf_dataset!r} is documentation only unless you patch the native script."
        )
    output_dir = Path(args.output_dir).expanduser()
    output_parent = output_dir.parent if output_dir.parent != Path("") else Path(".")
    if not output_parent.exists():
        report.warn(f"parent of --output-dir does not exist; os.mkdir will fail: {output_parent}")
    if output_dir.exists() and not output_dir.is_dir():
        report.error(f"--output-dir exists and is not a directory: {output_dir}")

    report.note(
        f"C-Eval source expects Hugging Face datasets.load_dataset('ceval/ceval-exam', task_name) for {CEVAL_TASK_COUNT} tasks."
    )
    report.note("The dev split is always used for few-shot examples; the selected split is used for scoring.")
    if args.offline:
        report.warn(
            "offline requested: ensure ceval/ceval-exam and all task configs/splits are already in the Hugging Face datasets cache."
        )
    if args.check_imports:
        check_imports(["datasets", "numpy", "torch", "tqdm", "transformers"], report)
    if args.check_cuda:
        check_cuda(report)

    repo = render_repo_path(args.repo_root)
    cmd = (
        f"cd {q(repo)} && python evaluation/evaluate_zh.py "
        f"--model_name_or_path {q(args.model)} "
        f"--shot {q(args.shot)} "
        f"--split {q(args.split)} "
        f"--output_dir {q(args.output_dir)}"
    )
    report.command(cmd)
    return report


def parse_categories_py(path: Path, report: Report) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception as exc:
        report.warn(f"could not parse categories.py safely: {exc}")
        return None, None

    found: Dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"subcategories", "categories"}:
                    try:
                        found[target.id] = ast.literal_eval(node.value)
                    except Exception as exc:
                        report.warn(f"could not literal-parse {target.id} in categories.py: {exc}")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {"subcategories", "categories"} and node.value is not None:
                try:
                    found[node.target.id] = ast.literal_eval(node.value)
                except Exception as exc:
                    report.warn(f"could not literal-parse {node.target.id} in categories.py: {exc}")
    subcategories = found.get("subcategories")
    categories = found.get("categories")
    if isinstance(subcategories, dict):
        report.note(f"parsed categories.py subcategories for {len(subcategories)} subjects")
    else:
        report.warn("categories.py did not expose a literal subcategories dict; subject mapping cannot be checked safely")
        subcategories = None
    if isinstance(categories, dict):
        report.note(f"parsed categories.py categories for {len(categories)} broad groups")
    else:
        report.warn("categories.py did not expose a literal categories dict; broad category mapping cannot be checked safely")
        categories = None
    return subcategories, categories


def read_csv_rows(path: Path, limit: int = 2) -> List[List[str]]:
    rows: List[List[str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            rows.append(row)
            if len(rows) >= limit:
                break
    return rows


def format_subject(subject: str) -> str:
    return "".join(" " + part for part in subject.split("_"))


def format_example(row: Sequence[str], include_answer: bool = True) -> str:
    if len(row) < 6:
        return ""
    prompt = row[0]
    # Native script uses all columns except first question and final answer as choices.
    k = len(row) - 2
    for idx in range(k):
        label = chr(ord("A") + idx)
        prompt += f"\n{label}. {row[idx + 1]}"
    prompt += "\nAnswer:"
    if include_answer:
        prompt += f" {row[k + 1]}\n\n"
    return prompt


def gen_prompt(dev_rows: Sequence[Sequence[str]], subject: str, k: int) -> str:
    prompt = f"The following are multiple choice questions (with answers) about {format_subject(subject)}.\n\n"
    if k == -1:
        k = len(dev_rows)
    for idx in range(min(k, len(dev_rows))):
        prompt += format_example(dev_rows[idx], include_answer=True)
    return prompt


def validate_mmlu_rows(subject: str, split_name: str, path: Path, report: Report) -> List[List[str]]:
    try:
        rows = read_csv_rows(path, limit=2)
    except Exception as exc:
        report.error(f"cannot read MMLU {split_name} CSV for {subject}: {path}: {exc}")
        return []
    if not rows:
        report.error(f"MMLU {split_name} CSV is empty for {subject}: {path}")
        return []
    for row_index, row in enumerate(rows):
        if len(row) < 6:
            report.error(
                f"MMLU {split_name} CSV row {row_index} for {subject} has {len(row)} columns; expected question + choices + answer"
            )
            continue
        answer = row[-1].strip().upper()
        if answer not in CHOICES:
            report.warn(
                f"MMLU {split_name} CSV row {row_index} for {subject} has non A-D answer label {row[-1]!r}"
            )
    return rows


def mmlu(args: argparse.Namespace) -> Report:
    report = Report(strict=args.strict)
    source_script = validate_repo_script(args.repo_root, "evaluation/evaluate_mmlu.py", report)
    validate_model_arg(args.model, args.allow_hf_id, report)
    if args.ntrain < 0:
        report.error("--ntrain must be non-negative")

    benchmark_root = Path(args.benchmark_root).expanduser().resolve()
    if not benchmark_root.exists():
        report.error(f"benchmark root does not exist: {benchmark_root}")
        # Continue to render useful diagnostics with best-effort paths.
    elif not benchmark_root.is_dir():
        report.error(f"benchmark root is not a directory: {benchmark_root}")

    categories_py = benchmark_root / "categories.py"
    subcategories: Optional[Dict[str, Any]] = None
    if not categories_py.exists():
        report.error(f"MMLU categories.py is missing: {categories_py}")
    else:
        subcategories, _ = parse_categories_py(categories_py, report)

    copied_script = benchmark_root / "evaluate_mmlu.py"
    if copied_script.exists():
        report.note(f"benchmark root already has evaluate_mmlu.py next to categories.py: {copied_script}")
    elif source_script and source_script.exists():
        report.warn(
            "evaluate_mmlu.py is not present in the benchmark root; copy the Baichuan script next to categories.py before running."
        )
    else:
        report.error(
            "cannot render a concrete MMLU copy/run workflow because neither benchmark-root/evaluate_mmlu.py nor repo-root/evaluation/evaluate_mmlu.py is available."
        )

    data_dir = resolve_relative(benchmark_root, args.data_dir)
    dev_dir = data_dir / "dev"
    test_dir = data_dir / "test"
    if not data_dir.exists():
        report.error(f"MMLU data dir does not exist: {data_dir}")
    if not dev_dir.exists():
        report.error(f"MMLU dev dir does not exist: {dev_dir}")
    if not test_dir.exists():
        report.error(f"MMLU test dir does not exist: {test_dir}")

    subjects: List[str] = []
    if test_dir.exists():
        subjects = sorted(path.name[: -len("_test.csv")] for path in test_dir.glob("*_test.csv"))
        if not subjects:
            report.error(f"no MMLU *_test.csv files found in {test_dir}")
        else:
            report.note(f"found {len(subjects)} MMLU test subjects")
    if dev_dir.exists() and subjects:
        missing_dev = [subject for subject in subjects if not (dev_dir / f"{subject}_dev.csv").exists()]
        if missing_dev:
            preview = ", ".join(missing_dev[:10])
            suffix = "..." if len(missing_dev) > 10 else ""
            report.error(f"missing paired dev CSV for {len(missing_dev)} subjects: {preview}{suffix}")
    if subcategories is not None and subjects:
        missing_category = [subject for subject in subjects if subject not in subcategories]
        if missing_category:
            preview = ", ".join(missing_category[:10])
            suffix = "..." if len(missing_category) > 10 else ""
            report.error(f"categories.py lacks subcategories for {len(missing_category)} subjects: {preview}{suffix}")

    sample_subjects = subjects[: max(0, args.sample_subjects)]
    for subject in sample_subjects:
        dev_path = dev_dir / f"{subject}_dev.csv"
        test_path = test_dir / f"{subject}_test.csv"
        dev_rows = validate_mmlu_rows(subject, "dev", dev_path, report) if dev_path.exists() else []
        test_rows = validate_mmlu_rows(subject, "test", test_path, report) if test_path.exists() else []
        if dev_rows and test_rows and args.prompt_max_chars > 0:
            prompt = gen_prompt(dev_rows, subject, min(args.ntrain, len(dev_rows))) + format_example(
                test_rows[0], include_answer=False
            )
            if len(prompt) > args.prompt_max_chars:
                report.warn(
                    f"sample prompt for {subject} is {len(prompt)} characters, above guard {args.prompt_max_chars}; "
                    "native MMLU truncates by token length >2048 and can loop awkwardly on very long examples."
                )
            zero_shot_prompt = gen_prompt([], subject, 0) + format_example(test_rows[0], include_answer=False)
            if len(zero_shot_prompt) > args.prompt_max_chars:
                report.warn(
                    f"zero-shot sample prompt for {subject} is {len(zero_shot_prompt)} characters; "
                    "if tokenized length stays above 2048, evaluate_mmlu.py may fail to make progress."
                )

    save_dir = resolve_relative(benchmark_root, args.save_dir)
    if save_dir.exists() and not save_dir.is_dir():
        report.error(f"--save-dir exists and is not a directory: {save_dir}")
    if "/" in args.model or os.sep in args.model:
        report.warn(
            "evaluate_mmlu.py uses the raw --model string in result directory and column names; slashes create nested paths/names."
        )
    if args.check_imports:
        check_imports(["numpy", "pandas", "torch", "transformers"], report)
    if args.check_cuda:
        check_cuda(report)

    repo = render_repo_path(args.repo_root)
    if not copied_script.exists():
        report.command(f"cp {q(Path(repo) / 'evaluation' / 'evaluate_mmlu.py')} {q(copied_script)}")
    data_arg = args.data_dir
    save_arg = args.save_dir
    report.command(
        f"cd {q(benchmark_root)} && python evaluate_mmlu.py "
        f"-m {q(args.model)} -d {q(data_arg)} -s {q(save_arg)} -k {q(args.ntrain)}"
    )
    return report


def add_common_model_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", help="Baichuan-7B source checkout containing evaluation/ scripts")
    parser.add_argument("--model", required=True, help="Baichuan checkpoint path or model id")
    parser.add_argument(
        "--allow-hf-id",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="allow a non-existing --model value to be treated as a model id/cache lookup",
    )
    parser.add_argument("--check-imports", action="store_true", help="import required Python packages without loading data/model weights")
    parser.add_argument("--check-cuda", action="store_true", help="check torch CUDA availability and a tiny allocation")
    parser.add_argument("--strict", action="store_true", help="treat warnings as a non-zero exit")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Baichuan-7B C-Eval/MMLU benchmark inputs and render native commands. "
            "No datasets are fetched and no benchmark inference is run."
        )
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    ceval_parser = subparsers.add_parser("ceval", help="preflight and render evaluation/evaluate_zh.py")
    add_common_model_args(ceval_parser)
    ceval_parser.add_argument("--shot", type=int, default=5, help="few-shot count for C-Eval dev examples")
    ceval_parser.add_argument("--split", default="val", help="C-Eval split to score; default matches evaluate_zh.py")
    ceval_parser.add_argument("--output-dir", default="ceval_output", help="C-Eval output directory")
    ceval_parser.add_argument(
        "--hf-dataset",
        default="ceval/ceval-exam",
        help="documentation label for the hard-coded C-Eval HF dataset source",
    )
    ceval_parser.add_argument("--offline", action="store_true", help="warn about required HF datasets cache state")
    ceval_parser.set_defaults(func=ceval)

    mmlu_parser = subparsers.add_parser("mmlu", help="preflight and render evaluation/evaluate_mmlu.py")
    add_common_model_args(mmlu_parser)
    mmlu_parser.add_argument("--benchmark-root", required=True, help="Hendrycks/test benchmark checkout root")
    mmlu_parser.add_argument("--data-dir", default="data", help="MMLU data directory, relative to benchmark root unless absolute")
    mmlu_parser.add_argument("--save-dir", default="results", help="MMLU save directory, relative to benchmark root unless absolute")
    mmlu_parser.add_argument("--ntrain", "-k", type=int, default=5, help="few-shot dev examples per subject")
    mmlu_parser.add_argument(
        "--sample-subjects",
        type=int,
        default=3,
        help="number of subjects to sample for CSV/prompt guards; use 0 to skip row checks",
    )
    mmlu_parser.add_argument(
        "--prompt-max-chars",
        type=int,
        default=12000,
        help="conservative character guard for prompt truncation risk; 0 disables",
    )
    mmlu_parser.set_defaults(func=mmlu)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report: Report = args.func(args)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        report.print_text()
    return report.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
