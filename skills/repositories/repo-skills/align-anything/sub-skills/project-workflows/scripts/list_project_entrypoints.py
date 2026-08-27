#!/usr/bin/env python3
"""Safely inventory Align-Anything satellite project entrypoints.

This script performs static inspection only. It reads text files, parses Python
ASTs, and summarizes shell snippets; it never imports Align-Anything, Janus,
Transformers, vLLM, Eval-Anything, or any project-local module, and it never
executes project scripts.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class KnownFile:
    path: str
    project: str
    category: str
    decision: str
    command_hint: str = ""
    runnable_when: str = ""
    notes: tuple[str, ...] = ()


@dataclass
class FileReport:
    path: str
    project: str
    category: str
    decision: str
    exists: bool
    command_hint: str = ""
    runnable_when: str = ""
    notes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    argparse_flags: list[str] = field(default_factory=list)
    has_main_guard: bool = False
    shell_commands: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    yaml_keys: list[str] = field(default_factory=list)
    error: str | None = None


KNOWN_FILES: tuple[KnownFile, ...] = (
    KnownFile(
        "projects/README.md",
        "projects",
        "readme",
        "context",
        notes=("Top-level project index; use to route to a satellite project.",),
    ),
    KnownFile(
        "projects/any_to_text/README.md",
        "any_to_text",
        "readme",
        "context",
        notes=("Documents Any-to-Text model builders and two-stage training pattern.",),
    ),
    KnownFile(
        "projects/any_to_text/build_llama_vision.py",
        "any_to_text",
        "python-entrypoint",
        "runnable-if-prepared",
        "python projects/any_to_text/build_llama_vision.py --language_model_path ... --vision_tower_path ... --save_path ...",
        "Requires accessible language model and CLIP vision tower; writes a saved model/processor directory.",
        ("Adds <image>, <unk>, and <pad> tokenizer tokens and builds a Llava-style model.",),
    ),
    KnownFile(
        "projects/any_to_text/build_llama_vision_audio.py",
        "any_to_text",
        "python-entrypoint",
        "runnable-if-prepared",
        "python projects/any_to_text/build_llama_vision_audio.py --language_model_path ... --vision_tower_path ... --audio_tower_path ... --save_path ...",
        "Requires Align-Anything vision-audio model wrapper plus accessible language, vision, and audio towers.",
        ("Validate the CLAP checkpoint id before running; README and script spelling differ slightly.",),
    ),
    KnownFile(
        "projects/janus/README.md",
        "janus",
        "readme",
        "optional-runtime",
        notes=("Janus workflows require a separate Janus-compatible package/runtime.",),
    ),
    KnownFile(
        "projects/janus/supervised_text_to_image.py",
        "janus",
        "python-entrypoint",
        "runnable-if-janus-runtime",
        "python projects/janus/supervised_text_to_image.py --input_path data.json --output_path train_tokenized.pt --model_path <janus-model> --num_gpus N",
        "Requires janus package, Janus model weights, CUDA plan, and JSON records with prompt/image.",
        ("Produces tokenized .pt records for generation SFT.",),
    ),
    KnownFile(
        "projects/janus/preference_text_to_image.py",
        "janus",
        "python-entrypoint",
        "runnable-if-janus-runtime",
        "python projects/janus/preference_text_to_image.py --input_path data.json --output_path train_tokenized.pt --model_path <janus-model> --num_gpus N",
        "Requires janus package, Janus model weights, CUDA plan, and JSON records with prompt/better_image/worse_image.",
        ("Produces better/worse token ids for generation preference learning.",),
    ),
    KnownFile(
        "scripts/janus/janus_sft_gen.sh",
        "janus",
        "shell-pattern",
        "runnable-if-janus-runtime",
        "bash scripts/janus/janus_sft_gen.sh",
        "Requires placeholder paths replaced, tokenized generation SFT data, DeepSpeed, and Janus runtime.",
    ),
    KnownFile(
        "scripts/janus/janus_dpo_gen.sh",
        "janus",
        "shell-pattern",
        "runnable-if-janus-runtime",
        "bash scripts/janus/janus_dpo_gen.sh",
        "Requires placeholder paths replaced, tokenized generation preference data, DeepSpeed, and Janus runtime.",
    ),
    KnownFile(
        "scripts/janus/janus_sft_und.sh",
        "janus",
        "shell-pattern",
        "runnable-if-janus-runtime",
        "bash scripts/janus/janus_sft_und.sh",
        "Requires placeholder paths replaced, text-image-to-text SFT data, DeepSpeed, and Janus runtime.",
    ),
    KnownFile(
        "scripts/janus/janus_dpo_und.sh",
        "janus",
        "shell-pattern",
        "runnable-if-janus-runtime",
        "bash scripts/janus/janus_dpo_und.sh",
        "Requires placeholder paths replaced, text-image-to-text preference data, DeepSpeed, and Janus runtime.",
    ),
    KnownFile(
        "projects/intermt/README.md",
        "intermt",
        "readme",
        "reference-only",
        notes=("Dataset and benchmark context; no safe in-repo runner evidenced.",),
    ),
    KnownFile(
        "projects/intermt/intermt_bench/README.md",
        "intermt",
        "readme",
        "reference-only",
        notes=("InterMT-Bench task description: score evaluation, pair comparison, crucial step recognition.",),
    ),
    KnownFile(
        "projects/lang_feedback/README.md",
        "lang_feedback",
        "readme",
        "internal-reference",
        notes=("README says the folder is under development and internal-use oriented.",),
    ),
    KnownFile(
        "projects/lang_feedback/base_gen.py",
        "lang_feedback",
        "python-entrypoint",
        "runnable-if-vllm-runtime",
        "python projects/lang_feedback/base_gen.py --model_name_or_path <model> --input_path data.json --output_dir out",
        "Requires vLLM multimodal runtime, images, GPUs, and prompt/image JSON fields.",
    ),
    KnownFile(
        "projects/lang_feedback/critique_gen.py",
        "lang_feedback",
        "python-entrypoint",
        "runnable-if-vllm-runtime",
        "python projects/lang_feedback/critique_gen.py --model_name_or_path <model> --input_path data.json --output_dir out",
        "Requires vLLM runtime and prompt/image/output_text JSON fields.",
    ),
    KnownFile(
        "projects/lang_feedback/refine_gen.py",
        "lang_feedback",
        "python-entrypoint",
        "runnable-if-vllm-runtime",
        "python projects/lang_feedback/refine_gen.py --model_name_or_path <model> --input_path data.json --output_dir out",
        "Requires vLLM runtime and prompt/image/output_text/critique JSON fields.",
    ),
    KnownFile(
        "projects/text_image_to_text_image/README.md",
        "text_image_to_text_image",
        "readme",
        "optional-runtime",
        notes=("Chameleon text-image interleaved workflow; requires compatible Transformers/model runtime.",),
    ),
    KnownFile(
        "projects/text_image_to_text_image/pre_tokenize_example.py",
        "text_image_to_text_image",
        "python-entrypoint",
        "runnable-if-chameleon-runtime",
        "python projects/text_image_to_text_image/pre_tokenize_example.py --input_path data.json --output_path data.pt --model_path <chameleon-model>",
        "Requires Chameleon processor/model wrapper and matching SFT-style data schema.",
    ),
    KnownFile(
        "projects/text_image_to_text_image/pre_tokenize_parallel_example.py",
        "text_image_to_text_image",
        "python-entrypoint",
        "runnable-if-chameleon-runtime",
        "python projects/text_image_to_text_image/pre_tokenize_parallel_example.py --input_path data.json --output_path data.pt --model_path <chameleon-model> --num_gpus N",
        "Requires Chameleon runtime; verify cache handling and GPU/process counts.",
    ),
    KnownFile(
        "projects/text_image_to_text_image/preference_tokenize_example.py",
        "text_image_to_text_image",
        "python-entrypoint",
        "runnable-if-chameleon-runtime",
        "python projects/text_image_to_text_image/preference_tokenize_example.py --input_path data.json --output_path data.pt --model_path <chameleon-model> --num_gpus N",
        "Requires Chameleon runtime and better/worse preference data schema.",
    ),
    KnownFile(
        "projects/text_image_to_text_image/prompt_only_tokenize_example.py",
        "text_image_to_text_image",
        "python-entrypoint",
        "runnable-if-chameleon-runtime",
        "python projects/text_image_to_text_image/prompt_only_tokenize_example.py --input_path data.json --output_path data.pt --model_path <chameleon-model> --num_gpus N",
        "Requires Chameleon runtime and prompt-only data schema.",
    ),
    KnownFile(
        "projects/eval-anything/README.md",
        "eval-anything",
        "readme",
        "reference-unless-runtime-prepared",
        notes=("Separate package/CLI/evaluation surface with heavy dependencies.",),
    ),
    KnownFile(
        "projects/eval-anything/pyproject.toml",
        "eval-anything",
        "package-metadata",
        "reference-unless-runtime-prepared",
        notes=("Declares package name eval-anything, Python >=3.11, broad evaluation dependencies, and optional vla extra.",),
    ),
    KnownFile(
        "projects/eval-anything/setup.py",
        "eval-anything",
        "package-metadata",
        "reference-unless-runtime-prepared",
        notes=("Declares console script eval-anything-cli = eval_anything.cli:main.",),
    ),
    KnownFile(
        "projects/eval-anything/eval_anything/cli.py",
        "eval-anything",
        "python-entrypoint",
        "reference-unless-runtime-prepared",
        "eval-anything-cli eval <config-file>",
        "Requires installed Eval-Anything package/runtime; CLI dispatches to python __main__.py.",
    ),
    KnownFile(
        "projects/eval-anything/eval_anything/__main__.py",
        "eval-anything",
        "python-entrypoint",
        "reference-unless-runtime-prepared",
        "python -m eval_anything --eval_info evaluate.yaml",
        "Requires Eval-Anything runtime, model backend, config, and benchmark data.",
    ),
    KnownFile(
        "projects/eval-anything/eval_anything/configs/evaluate.yaml",
        "eval-anything",
        "config",
        "reference-unless-runtime-prepared",
        notes=("Default-style evaluation config with eval_cfgs/model_cfgs/infer_cfgs sections.",),
    ),
    KnownFile(
        "projects/eval-anything/eval_anything/pipeline/base_task.py",
        "eval-anything",
        "pipeline-module",
        "reference-unless-runtime-prepared",
        notes=("Loads configs, model backend, benchmarks, and saves results.",),
    ),
    KnownFile(
        "projects/eval-anything/eval_anything/pipeline/base_benchmark.py",
        "eval-anything",
        "pipeline-module",
        "reference-unless-runtime-prepared",
        notes=("Benchmark base class with modality map, dataloading, inference, metrics, and result save hooks.",),
    ),
    KnownFile(
        "projects/eval-anything/scripts/run.sh",
        "eval-anything",
        "shell-pattern",
        "reference-unless-runtime-prepared",
        "bash projects/eval-anything/scripts/run.sh",
        "Requires Eval-Anything runtime and configured package-local YAML.",
    ),
    KnownFile(
        "projects/eval-anything/scripts/run_vla.sh",
        "eval-anything",
        "shell-pattern",
        "reference-unless-runtime-prepared",
        "bash projects/eval-anything/scripts/run_vla.sh",
        "Requires VLA assets, optional dependencies, and compatible runtime.",
    ),
)


PROJECT_SUMMARY = {
    "any_to_text": "Any-to-Text builders are runnable only after model/checkpoint access and output write intent are confirmed.",
    "janus": "Janus workflows need a separate Janus-compatible package and CUDA-capable tokenization/training plan.",
    "intermt": "InterMT is reference-only by default: dataset/benchmark documentation, not a local runner.",
    "lang_feedback": "Language feedback scripts are internal/development vLLM patterns with heavy GPU assumptions.",
    "text_image_to_text_image": "Text-image-to-text-image workflows require a Chameleon-capable runtime and schema-aware tokenization.",
    "eval-anything": "Eval-Anything is a separate heavy evaluation package; treat as reference unless that runtime is prepared.",
}


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


class PythonVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[str] = []
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.argparse_flags: list[str] = []
        self.has_main_guard = False

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        self.imports.extend(alias.name for alias in node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        prefix = "." * node.level
        module = f"{prefix}{node.module or ''}"
        imported = ",".join(alias.name for alias in node.names)
        self.imports.append(f"{module}:{imported}" if module else imported)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    self.argparse_flags.append(arg.value)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        if self._is_main_guard(node.test):
            self.has_main_guard = True
        self.generic_visit(node)

    @staticmethod
    def _is_main_guard(test: ast.expr) -> bool:
        if not isinstance(test, ast.Compare):
            return False
        left = test.left
        comparators = test.comparators
        if not comparators:
            return False
        left_is_name = isinstance(left, ast.Name) and left.id == "__name__"
        value_is_main = any(isinstance(c, ast.Constant) and c.value == "__main__" for c in comparators)
        return left_is_name and value_is_main


def inspect_python(path: Path, report: FileReport) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        report.error = f"syntax error during static parse: {exc}"
        return
    visitor = PythonVisitor()
    visitor.visit(tree)
    report.imports = unique_preserve_order(visitor.imports)[:20]
    report.functions = unique_preserve_order(visitor.functions)[:30]
    report.classes = unique_preserve_order(visitor.classes)[:20]
    report.argparse_flags = unique_preserve_order(visitor.argparse_flags)[:30]
    report.has_main_guard = visitor.has_main_guard


def inspect_shell(path: Path, report: FileReport) -> None:
    commands: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.search(r"\b(deepspeed|python|bash|source|export|eval-anything-cli)\b", stripped):
            commands.append(stripped)
    report.shell_commands = commands[:20]


def inspect_readme(path: Path, report: FileReport) -> None:
    headings: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            headings.append(line.strip())
    report.headings = headings[:30]


def inspect_yaml_or_toml(path: Path, report: FileReport) -> None:
    keys: list[str] = []
    pattern = re.compile(r"^\s{0,4}([A-Za-z_][A-Za-z0-9_.-]*):")
    toml_pattern = re.compile(r"^\s*\[([^\]]+)\]")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            keys.append(match.group(1))
            continue
        match = toml_pattern.match(line)
        if match:
            keys.append(f"[{match.group(1)}]")
    report.yaml_keys = unique_preserve_order(keys)[:40]


def report_for_known(root: Path, known: KnownFile) -> FileReport:
    path = root / known.path
    report = FileReport(
        path=known.path,
        project=known.project,
        category=known.category,
        decision=known.decision,
        exists=path.exists(),
        command_hint=known.command_hint,
        runnable_when=known.runnable_when,
        notes=list(known.notes),
    )
    if not report.exists:
        return report
    if path.suffix == ".py":
        inspect_python(path, report)
    elif path.suffix == ".sh":
        inspect_shell(path, report)
    elif path.name.lower() == "readme.md" or path.suffix.lower() == ".md":
        inspect_readme(path, report)
    elif path.suffix.lower() in {".yaml", ".yml", ".toml"}:
        inspect_yaml_or_toml(path, report)
    return report


def dynamic_known_files(root: Path, max_configs: int) -> list[KnownFile]:
    existing = {item.path for item in KNOWN_FILES}
    dynamic: list[KnownFile] = []

    for path in sorted((root / "projects/eval-anything/eval_anything/configs").glob("*.yaml"))[:max_configs]:
        rel = rel_path(path, root)
        if rel not in existing:
            dynamic.append(
                KnownFile(
                    rel,
                    "eval-anything",
                    "config",
                    "reference-unless-runtime-prepared",
                    notes=("Additional Eval-Anything evaluation config discovered statically.",),
                )
            )

    for path in sorted((root / "projects/eval-anything/eval_anything/pipeline").glob("*.py")):
        rel = rel_path(path, root)
        if rel not in existing:
            dynamic.append(
                KnownFile(
                    rel,
                    "eval-anything",
                    "pipeline-module",
                    "reference-unless-runtime-prepared",
                    notes=("Additional Eval-Anything pipeline module discovered statically.",),
                )
            )

    return dynamic


def build_inventory(root: Path, max_configs: int) -> dict[str, object]:
    known = list(KNOWN_FILES) + dynamic_known_files(root, max_configs=max_configs)
    reports = [report_for_known(root, item) for item in known]
    by_project: dict[str, int] = {}
    missing: list[str] = []
    for report in reports:
        by_project[report.project] = by_project.get(report.project, 0) + int(report.exists)
        if not report.exists:
            missing.append(report.path)
    return {
        "static_only": True,
        "executes_project_code": False,
        "imports_project_modules": False,
        "project_summary": PROJECT_SUMMARY,
        "existing_counts_by_project": by_project,
        "missing_known_paths": missing,
        "files": [asdict(report) for report in reports],
    }


def print_text(inventory: dict[str, object]) -> None:
    print("Static Align-Anything project entrypoint inventory")
    print("- project code executed: no")
    print("- project modules imported: no")
    print()
    print("Project decisions:")
    for project, summary in inventory["project_summary"].items():  # type: ignore[union-attr]
        count = inventory["existing_counts_by_project"].get(project, 0)  # type: ignore[index]
        print(f"- {project} ({count} known files present): {summary}")
    print()

    missing = inventory["missing_known_paths"]
    if missing:  # type: ignore[truthy-function]
        print("Missing known paths:")
        for path in missing:  # type: ignore[union-attr]
            print(f"- {path}")
        print()

    print("Files:")
    for item in inventory["files"]:  # type: ignore[union-attr]
        status = "present" if item["exists"] else "missing"
        print(f"\n[{status}] {item['path']}")
        print(f"  project: {item['project']} | category: {item['category']} | decision: {item['decision']}")
        if item.get("command_hint"):
            print(f"  command hint: {item['command_hint']}")
        if item.get("runnable_when"):
            print(f"  runnable when: {item['runnable_when']}")
        for note in item.get("notes", []):
            print(f"  note: {note}")
        if item.get("error"):
            print(f"  parse error: {item['error']}")
        if item.get("argparse_flags"):
            print("  argparse flags: " + ", ".join(item["argparse_flags"]))
        if item.get("functions"):
            print("  functions: " + ", ".join(item["functions"][:12]))
        if item.get("classes"):
            print("  classes: " + ", ".join(item["classes"][:12]))
        if item.get("imports"):
            print("  imports: " + ", ".join(item["imports"][:10]))
        if item.get("has_main_guard"):
            print("  has __main__ guard: yes")
        if item.get("shell_commands"):
            print("  shell command patterns:")
            for cmd in item["shell_commands"][:8]:
                print(f"    - {cmd}")
        if item.get("headings"):
            print("  headings: " + " | ".join(item["headings"][:8]))
        if item.get("yaml_keys"):
            print("  config/package keys: " + ", ".join(item["yaml_keys"][:12]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically list Align-Anything satellite project entrypoints without imports or execution."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to inspect. Defaults to the current working directory.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument(
        "--max-configs",
        type=int,
        default=8,
        help="Maximum additional Eval-Anything YAML configs to include beyond the default config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"repository root does not exist or is not a directory: {args.root}")
    inventory = build_inventory(root, max_configs=max(args.max_configs, 0))
    if args.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    else:
        print_text(inventory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
