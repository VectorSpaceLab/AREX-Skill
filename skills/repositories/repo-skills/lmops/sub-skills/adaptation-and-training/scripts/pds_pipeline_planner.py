#!/usr/bin/env python3
"""Stage checklist and path-placeholder validator for PDS planning.

This helper never launches training, inference, tokenization, or downloads.
It only validates that a proposed data-selection plan has the expected stages
and that path-like values are either concrete or intentionally left unset.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PATH_HINTS = ("dir", "path", "checkpoint", "root", "file", "cache")
PLACEHOLDER_MARKERS = ("<", ">", "todo", "replace", "path/to", "fill-me", "???", "unset")

DEFAULTS = {
    "raw_cc_dir": "pretrain_data/redpajama/cc_en_head",
    "tokenized_cc_dir": "processed_data/pretrain/cc/mistral-1025",
    "converted_cc_dir": "processed_data/data_scorer_infer/cc/mistral-fairseq-1024",
    "proxy_dir": "processed_data/proxy/cc-mistral-1025/163840",
    "lima_dir": "pretrain_data/lima",
    "lima_tokenized_dir": "processed_data/lima/mistral-1025/dev",
    "baseline_checkpoint": "results/pretrain/mistral_160M-10K",
    "baseline_results_dir": "results/pretrain",
    "pmp_results_dir": "results/pmp_solver",
    "pmp_proxy_dir": "processed_data/proxy/cc-mistral-1025/163840",
    "proxy_score_path": "results/pmp_solver/cc-lima/160M-10k/sgd-t100-bs8-lr0.008constant1e-07-G2-N16-NN2ct10",
    "scorer_tokenizer_path": "checkpoints/fairseq/125M",
    "data_scorer_checkpoint": "results/data_scorer",
    "scorer_train_dir": "processed_data/data_scorer_train/cc-sgd100-160M-10k-lima-163840",
    "scorer_infer_dir": "results/data_scorer_infer/cc/cc-sgd100-160M-10k-lima",
    "selected_pretrain_dir": "processed_data/pretrain/cc-sgd100-160M-10k-lima",
    "pds_results_dir": "results/pretrain",
    "dclm_dir": "pretrain_data/dclm",
    "eval_results_dir": "results/eval_offline",
    "deepspeed_config": "configs/deepspeed/ds_config.json",
    "proxy_num": 163840,
    "ds_ratio": 0.4,
    "ds_gumbel_temperature": 0.1,
}

STAGES = [
    {
        "name": "tokenize_cc",
        "concept": "Tokenize the large CC-style corpus for pre-training.",
        "requires": ["raw_cc_dir", "tokenized_cc_dir", "baseline_checkpoint"],
        "produces": ["tokenized_cc_dir"],
    },
    {
        "name": "convert_tokenization",
        "concept": "Convert the tokenized corpus to the scorer tokenizer family.",
        "requires": ["tokenized_cc_dir", "converted_cc_dir", "baseline_checkpoint", "scorer_tokenizer_path"],
        "produces": ["converted_cc_dir"],
    },
    {
        "name": "sample_proxy",
        "concept": "Sample the proxy subset used by the PMP solver.",
        "requires": ["tokenized_cc_dir", "proxy_dir", "proxy_num"],
        "produces": ["proxy_dir"],
    },
    {
        "name": "pretrain_baseline",
        "concept": "Train the small baseline model that seeds the control problem.",
        "requires": ["tokenized_cc_dir", "baseline_checkpoint", "baseline_results_dir"],
        "produces": ["baseline_results_dir"],
    },
    {
        "name": "prepare_lima",
        "concept": "Tokenize the LIMA-style dev set used by the PMP solver.",
        "requires": ["lima_dir", "lima_tokenized_dir", "baseline_checkpoint"],
        "produces": ["lima_tokenized_dir"],
    },
    {
        "name": "solve_pmp",
        "concept": "Run the PMP solver on the proxy and dev data.",
        "requires": ["baseline_results_dir", "tokenized_cc_dir", "proxy_dir", "lima_tokenized_dir", "pmp_results_dir"],
        "produces": ["pmp_results_dir"],
    },
    {
        "name": "prepare_scorer_train",
        "concept": "Build scorer training data from proxy scores.",
        "requires": ["proxy_score_path", "scorer_train_dir", "scorer_tokenizer_path"],
        "produces": ["scorer_train_dir"],
    },
    {
        "name": "train_data_scorer",
        "concept": "Train the data scorer on the proxy-derived labels.",
        "requires": ["scorer_train_dir", "data_scorer_checkpoint", "deepspeed_config"],
        "produces": ["data_scorer_checkpoint"],
    },
    {
        "name": "infer_data_scorer",
        "concept": "Infer scores for the large corpus.",
        "requires": ["converted_cc_dir", "data_scorer_checkpoint", "scorer_infer_dir"],
        "produces": ["scorer_infer_dir"],
    },
    {
        "name": "select_pretrain_data",
        "concept": "Select the final corpus using score files and selection ratios.",
        "requires": ["tokenized_cc_dir", "scorer_infer_dir", "selected_pretrain_dir", "scorer_tokenizer_path", "ds_ratio", "ds_gumbel_temperature"],
        "produces": ["selected_pretrain_dir"],
    },
    {
        "name": "pretrain_pds",
        "concept": "Train the selected-data model and compare it to the baseline.",
        "requires": ["selected_pretrain_dir", "pds_results_dir"],
        "produces": ["pds_results_dir"],
    },
    {
        "name": "evaluate",
        "concept": "Run offline evaluation on the selected and baseline models.",
        "requires": ["dclm_dir", "eval_results_dir", "baseline_results_dir", "pds_results_dir"],
        "produces": ["eval_results_dir"],
    },
]


def _is_path_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in PATH_HINTS)


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, (int, float, bool)):
        return False
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def _path_exists(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float, bool)):
        return True
    try:
        return Path(str(value)).expanduser().exists()
    except Exception:
        return False


def _load_plan(path: Path | None) -> Dict[str, Any]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("plan JSON must be an object")
    return loaded


def _parse_set_values(pairs: Iterable[str]) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"expected key=value, got: {item}")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty key in override: {item}")
        try:
            value = json.loads(raw_value)
        except Exception:
            value = raw_value
        values[key] = value
    return values


@dataclass
class StageReport:
    name: str
    concept: str
    status: str
    required: List[str]
    missing: List[str]
    unresolved: List[str]
    ready_inputs: List[str]
    produced: List[str]


def _resolve_plan(base_path: Path | None, loaded: Dict[str, Any], overrides: Dict[str, Any], fill_defaults: bool) -> Dict[str, Any]:
    plan: Dict[str, Any] = {}
    if fill_defaults:
        plan.update(DEFAULTS)
    if loaded:
        plan.update(loaded)
    plan.update(overrides)

    if base_path is not None:
        plan["base_path"] = str(base_path)
        if fill_defaults:
            root = base_path
            for key, rel in list(DEFAULTS.items()):
                if _is_path_key(key) and str(plan.get(key, "")) == str(rel):
                    plan[key] = str(root / rel)

    # Provide a few useful derived aliases when the caller only names one location.
    baseline_ckpt = plan.get("baseline_checkpoint")
    if "baseline_results_dir" not in plan and not _is_placeholder(baseline_ckpt):
        plan["baseline_results_dir"] = str(Path(str(baseline_ckpt)).parent)
    selected_dir = plan.get("selected_pretrain_dir")
    if "pds_results_dir" not in plan and not _is_placeholder(selected_dir):
        plan["pds_results_dir"] = str(Path(str(selected_dir)).parent)

    return plan


def _make_stage_report(stage: Dict[str, Any], plan: Dict[str, Any], check_exists: bool) -> StageReport:
    required = list(stage["requires"])
    missing: List[str] = []
    unresolved: List[str] = []
    ready_inputs: List[str] = []

    for key in required:
        value = plan.get(key)
        if _is_placeholder(value):
            unresolved.append(key)
            missing.append(key)
            continue
        if _is_path_key(key) and check_exists and not _path_exists(value):
            missing.append(key)
            continue
        ready_inputs.append(key)

    status = "READY" if not missing else "BLOCKED"
    return StageReport(
        name=stage["name"],
        concept=stage["concept"],
        status=status,
        required=required,
        missing=missing,
        unresolved=unresolved,
        ready_inputs=ready_inputs,
        produced=list(stage["produces"]),
    )


def _render_markdown(plan: Dict[str, Any], stages: List[StageReport]) -> str:
    lines = ["# PDS pipeline plan", ""]
    lines.append("## Plan summary")
    lines.append("")
    interesting_keys = [
        "base_path",
        "raw_cc_dir",
        "tokenized_cc_dir",
        "converted_cc_dir",
        "proxy_dir",
        "lima_dir",
        "lima_tokenized_dir",
        "baseline_checkpoint",
        "scorer_tokenizer_path",
        "data_scorer_checkpoint",
        "scorer_train_dir",
        "scorer_infer_dir",
        "selected_pretrain_dir",
        "dclm_dir",
        "eval_results_dir",
        "proxy_num",
        "ds_ratio",
        "ds_gumbel_temperature",
    ]
    for key in interesting_keys:
        if key in plan:
            lines.append(f"- {key}: {plan[key]}")
    lines.append("")
    lines.append("## Stage checklist")
    lines.append("")
    for stage in stages:
        lines.append(f"### {stage.name}")
        lines.append(f"- status: {stage.status}")
        lines.append(f"- concept: {stage.concept}")
        lines.append(f"- required: {', '.join(stage.required) if stage.required else 'none'}")
        lines.append(f"- ready inputs: {', '.join(stage.ready_inputs) if stage.ready_inputs else 'none'}")
        lines.append(f"- missing: {', '.join(stage.missing) if stage.missing else 'none'}")
        lines.append(f"- produces: {', '.join(stage.produced) if stage.produced else 'none'}")
        lines.append("")
    blocked = [stage.name for stage in stages if stage.status != "READY"]
    lines.append("## Overall status")
    lines.append("")
    lines.append("- ready" if not blocked else f"- blocked stages: {', '.join(blocked)}")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This planner does not launch any training or inference jobs.")
    lines.append("- Treat a missing path as a planning blocker only when that path is part of the current stage.")
    lines.append("- Use a separate execution environment to run the heavy PDS workflow after the plan is approved.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-path", type=Path, help="Workspace root used to fill default relative paths.")
    parser.add_argument("--plan-json", type=Path, help="Optional JSON plan file with path and scalar values.")
    parser.add_argument("--set", dest="overrides", action="append", default=[], help="Override a plan key as key=value. Values are parsed as JSON when possible.")
    parser.add_argument("--fill-defaults", action="store_true", help="Populate common PDS paths from the base path.")
    parser.add_argument("--check-exists", action="store_true", help="Check whether concrete path-like values exist on disk.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of markdown.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when any stage is blocked.")
    parser.add_argument("--write-template", type=Path, help="Write a JSON template plan to this file and exit.")
    return parser.parse_args()


def _template_payload() -> Dict[str, Any]:
    template = {key: (f"<{key}>" if _is_path_key(key) else value) for key, value in DEFAULTS.items()}
    template["base_path"] = "<workspace-root>"
    return template


def main() -> int:
    args = parse_args()

    if args.write_template is not None:
        args.write_template.parent.mkdir(parents=True, exist_ok=True)
        args.write_template.write_text(json.dumps(_template_payload(), indent=2) + "\n", encoding="utf-8")
        print(f"wrote template: {args.write_template}")
        return 0

    loaded = _load_plan(args.plan_json)
    overrides = _parse_set_values(args.overrides)
    plan = _resolve_plan(args.base_path, loaded, overrides, args.fill_defaults)

    stage_reports = [_make_stage_report(stage, plan, args.check_exists) for stage in STAGES]
    blocked = [stage for stage in stage_reports if stage.status != "READY"]

    if args.json:
        print(json.dumps({
            "plan": plan,
            "stages": [asdict(stage) for stage in stage_reports],
            "overall_status": "READY" if not blocked else "BLOCKED",
        }, indent=2))
    else:
        print(_render_markdown(plan, stage_reports))

    if args.strict and blocked:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
