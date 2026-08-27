#!/usr/bin/env python3
"""Static inspector for RLinf reasoning, agentic, coding online RL, and SFT YAMLs.

The script is intentionally read-only: it parses YAML files, prints a summary,
and reports risky missing fields before an expensive RLinf launch.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - environment-specific message
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

MISSING = object()
PLACEHOLDER_PATTERNS = (
    "/path/to",
    "/PATH/TO",
    "TODO",
    "todo",
    "LLM_JUDGE_IP",
    "LLM_JUDGE_PORT",
    "your_",
    "xx.xx.xx.xx",
)
SUPPORTED_ROLLOUT_BACKENDS = {"sglang", "vllm"}
SUPPORTED_TRAINING_BACKENDS = {"megatron", "fsdp", "fsdp2"}


class NoDatesSafeLoader(yaml.SafeLoader if yaml else object):
    """PyYAML safe loader that leaves timestamp-like scalars as strings."""


if yaml:
    # Avoid surprising date coercion while preserving normal YAML parsing.
    for ch, resolvers in list(NoDatesSafeLoader.yaml_implicit_resolvers.items()):
        NoDatesSafeLoader.yaml_implicit_resolvers[ch] = [
            (tag, regexp)
            for tag, regexp in resolvers
            if tag != "tag:yaml.org,2002:timestamp"
        ]


def dot_get(data: Any, path: str, default: Any = MISSING) -> Any:
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def is_missing(value: Any) -> bool:
    return value is MISSING or value is None


def stringify(value: Any) -> str:
    if value is MISSING:
        return "<missing>"
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def normalize_components(raw: Any) -> dict[str, Any]:
    """Expand RLinf component_placement keys such as 'actor,rollout,reward'."""
    out: dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        for part in str(key).split(","):
            name = part.strip()
            if name:
                out[name] = value
    return out


def placeholder(value: Any) -> bool:
    if value is MISSING or value is None:
        return False
    if isinstance(value, list):
        return any(placeholder(v) for v in value)
    if isinstance(value, dict):
        return any(placeholder(v) for v in value.values())
    text = str(value)
    return any(p in text for p in PLACEHOLDER_PATTERNS)


def concrete(value: Any) -> bool:
    if value is MISSING or value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return not placeholder(value)


def resolve_simple(value: Any, cfg: dict[str, Any]) -> int | None:
    """Resolve ints and common RLinf OmegaConf expressions used for token budgets."""
    direct = to_int(value)
    if direct is not None:
        return direct
    if not isinstance(value, str):
        return None
    text = value.replace(" ", "")
    if text == "${runner.seq_length}":
        return to_int(dot_get(cfg, "runner.seq_length"))
    if text == "${data.max_prompt_length}":
        return to_int(dot_get(cfg, "data.max_prompt_length"))
    if text.startswith("${subtract:") and "runner.seq_length" in text and "data.max_prompt_length" in text:
        seq = to_int(dot_get(cfg, "runner.seq_length"))
        prompt = to_int(dot_get(cfg, "data.max_prompt_length"))
        if seq is not None and prompt is not None:
            return seq - prompt
    # Resolve a literal subtract expression with numeric terms.
    m = re.fullmatch(r"\$\{subtract:([0-9]+),([0-9]+)\}", text)
    if m:
        return int(m.group(1)) - int(m.group(2))
    return None


def add_issue(issues: list[dict[str, str]], severity: str, message: str) -> None:
    issues.append({"severity": severity, "message": message})


def env_status(names: list[str]) -> dict[str, str]:
    return {name: ("set" if os.environ.get(name) else "missing") for name in names}


def infer_workflow(cfg: dict[str, Any]) -> str:
    task_type = dot_get(cfg, "runner.task_type", "")
    data_type = dot_get(cfg, "data.type", "")
    reward_type = dot_get(cfg, "reward.reward_type", "")
    parser = dot_get(cfg, "agentloop.toolcall_parser", "")
    if task_type == "coding_online_rl":
        return "coding-online-rl"
    if task_type == "sft":
        model_type = stringify(dot_get(cfg, "actor.model.model_type", ""))
        if "resnet" in model_type or dot_get(cfg, "runner.early_stop", None):
            return "sft-or-reward-model"
        if data_type == "vlm":
            return "vlm-sft"
        return "sft"
    if "wideseek" in stringify(parser) or data_type == "wideseek_r1":
        return "wideseek-r1"
    if "rstar2" in stringify(parser) or data_type == "rstar2" or reward_type == "rstar2":
        return "rstar2"
    if "searchr1" in stringify(parser) or reward_type == "searchr1":
        return "searchr1"
    if reward_type == "code_offline":
        return "offline-code-judge"
    if data_type == "vlm":
        return "vlm-reasoning"
    if dot_get(cfg, "agentloop", None) is not None:
        return "agentic-rl"
    if dot_get(cfg, "critic.use_critic_model", False) is True or dot_get(cfg, "algorithm.adv_type", "") == "gae":
        return "reasoning-ppo"
    if task_type in {"reasoning", "reasoning_eval"}:
        return "reasoning-rl"
    return "unknown"


def inspect_config(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required to parse YAML files: {YAML_IMPORT_ERROR}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            cfg = yaml.load(fh, Loader=NoDatesSafeLoader)
    except Exception as exc:
        return {
            "path": str(path),
            "parse_error": str(exc),
            "issues": [{"severity": "error", "message": f"YAML parse failed: {exc}"}],
        }
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        return {
            "path": str(path),
            "parse_error": "top-level YAML is not a mapping",
            "issues": [{"severity": "error", "message": "Top-level YAML must be a mapping."}],
        }

    issues: list[dict[str, str]] = []
    components = normalize_components(dot_get(cfg, "cluster.component_placement", {}))
    workflow = infer_workflow(cfg)

    task_type = dot_get(cfg, "runner.task_type")
    actor_backend = dot_get(cfg, "actor.training_backend")
    rollout_backend = dot_get(cfg, "rollout.rollout_backend")
    adv_type = dot_get(cfg, "algorithm.adv_type")
    loss_type = dot_get(cfg, "algorithm.loss_type")
    group_size = dot_get(cfg, "algorithm.group_size")
    recompute_logprobs = dot_get(cfg, "algorithm.recompute_logprobs")
    return_logprobs = dot_get(cfg, "rollout.return_logprobs")
    seq_length = dot_get(cfg, "runner.seq_length")
    max_prompt_length = dot_get(cfg, "data.max_prompt_length")
    algorithm_max_new_tokens = dot_get(cfg, "algorithm.sampling_params.max_new_tokens")
    rollout_max_new_tokens = dot_get(cfg, "rollout.sampling_params.max_new_tokens")
    max_new_tokens = algorithm_max_new_tokens
    if max_new_tokens is MISSING and rollout_max_new_tokens is not MISSING:
        max_new_tokens = rollout_max_new_tokens

    # General required fields.
    for field in ("runner.task_type", "cluster.num_nodes", "runner.output_dir", "runner.experiment_name"):
        value = dot_get(cfg, field)
        if is_missing(value):
            add_issue(issues, "warn", f"Missing {field}; launchers or loggers may need it.")
        elif placeholder(value):
            add_issue(issues, "warn", f"{field} still looks like a placeholder: {stringify(value)}")

    if actor_backend is not MISSING and actor_backend not in SUPPORTED_TRAINING_BACKENDS:
        add_issue(issues, "warn", f"actor.training_backend is {actor_backend!r}; expected one of {sorted(SUPPORTED_TRAINING_BACKENDS)}.")

    if workflow not in {"sft", "vlm-sft", "sft-or-reward-model"}:
        if is_missing(rollout_backend):
            add_issue(issues, "error", "Missing rollout.rollout_backend for RL/eval workflow.")
        elif rollout_backend not in SUPPORTED_ROLLOUT_BACKENDS:
            add_issue(issues, "error", f"Unsupported rollout.rollout_backend {rollout_backend!r}; expected sglang or vllm.")
        for comp in ("actor", "rollout"):
            if comp not in components and not components:
                add_issue(issues, "warn", "cluster.component_placement is missing or not a mapping.")
                break
            if components and comp not in components:
                add_issue(issues, "warn", f"component_placement has no {comp!r} component.")
    else:
        if "actor" not in components and components:
            add_issue(issues, "warn", "SFT/reward training config usually needs an actor placement component.")

    # Paths and placeholders.
    important_paths = [
        "rollout.model.model_path",
        "actor.model.model_path",
        "actor.tokenizer.tokenizer_model",
        "data.train_data_paths",
        "data.val_data_paths",
        "data.eval_data_paths",
        "runner.output_dir",
    ]
    for field in important_paths:
        value = dot_get(cfg, field)
        if value is not MISSING and placeholder(value):
            add_issue(issues, "warn", f"{field} contains a placeholder: {stringify(value)}")

    # Length budget.
    seq_i = resolve_simple(seq_length, cfg)
    prompt_i = resolve_simple(max_prompt_length, cfg)
    max_new_i = resolve_simple(max_new_tokens, cfg)
    if workflow not in {"sft-or-reward-model"}:
        if seq_i is None:
            add_issue(issues, "warn", "runner.seq_length is missing or not statically resolvable.")
        if prompt_i is None and workflow not in {"sft"}:
            add_issue(issues, "warn", "data.max_prompt_length is missing or not statically resolvable.")
        if seq_i is not None and prompt_i is not None:
            if seq_i <= prompt_i:
                add_issue(issues, "error", f"runner.seq_length ({seq_i}) must exceed data.max_prompt_length ({prompt_i}).")
            elif seq_i - prompt_i < 128 and workflow not in {"sft", "vlm-sft"}:
                add_issue(issues, "warn", f"Generation budget is only {seq_i - prompt_i} tokens.")
        if max_new_i is not None and max_new_i <= 0:
            add_issue(issues, "error", f"sampling max_new_tokens resolves to {max_new_i}.")
        if max_new_i is not None and seq_i is not None and prompt_i is not None and seq_i > prompt_i:
            budget = seq_i - prompt_i
            if max_new_i > budget:
                add_issue(
                    issues,
                    "error",
                    "sampling max_new_tokens "
                    f"({max_new_i}) exceeds runner.seq_length - data.max_prompt_length ({budget}).",
                )
        if algorithm_max_new_tokens is MISSING and rollout_max_new_tokens is not MISSING:
            add_issue(
                issues,
                "warn",
                "Found rollout.sampling_params.max_new_tokens; RLinf reasoning configs usually place this under algorithm.sampling_params.max_new_tokens.",
            )
        if max_new_tokens is MISSING and workflow not in {"sft", "vlm-sft", "sft-or-reward-model"}:
            add_issue(issues, "warn", "Missing algorithm.sampling_params.max_new_tokens.")

    # Algorithm consistency.
    group_i = to_int(group_size)
    if adv_type == "grpo" and (group_i is None or group_i <= 1):
        add_issue(issues, "warn", "GRPO usually requires algorithm.group_size >= 2 for relative advantages.")
    if stringify(adv_type).startswith("grpo") and group_i == 1:
        add_issue(issues, "warn", "Group-relative workflow has group_size 1; check whether PPO/raw advantage was intended.")
    if adv_type == "gae":
        critic_enabled = to_bool(dot_get(cfg, "critic.use_critic_model"))
        if critic_enabled is not True and workflow != "coding-online-rl":
            add_issue(issues, "warn", "GAE/PPO reasoning usually needs critic.use_critic_model: true.")
        if group_i not in (None, 1):
            add_issue(issues, "warn", "PPO/GAE reasoning usually uses algorithm.group_size: 1.")
    if to_bool(recompute_logprobs) is False and to_bool(return_logprobs) is False:
        add_issue(issues, "error", "Both recompute_logprobs and rollout.return_logprobs are false; actor may have no old logprobs.")

    # Backend-specific blocks.
    if actor_backend == "megatron":
        for field in ("actor.megatron", "actor.tokenizer", "actor.model.tensor_model_parallel_size", "actor.model.pipeline_model_parallel_size"):
            if dot_get(cfg, field) is MISSING:
                add_issue(issues, "warn", f"Megatron actor missing {field}.")
    if actor_backend in {"fsdp", "fsdp2"}:
        if dot_get(cfg, "actor.fsdp_config") is MISSING:
            add_issue(issues, "warn", "FSDP actor missing actor.fsdp_config.")
    if rollout_backend == "sglang" and dot_get(cfg, "rollout.sglang") is MISSING:
        add_issue(issues, "warn", "SGLang rollout selected but rollout.sglang block is missing.")
    if rollout_backend == "vllm" and dot_get(cfg, "rollout.vllm") is MISSING:
        add_issue(issues, "warn", "vLLM rollout selected but rollout.vllm block is missing.")

    # Workflow-specific checks.
    external: dict[str, Any] = {}
    if workflow == "coding-online-rl":
        if rollout_backend != "sglang":
            add_issue(issues, "error", "coding_online_rl path expects SGLang rollout.")
        if to_bool(recompute_logprobs) is not True:
            add_issue(issues, "error", "coding_online_rl runner asserts algorithm.recompute_logprobs: true.")
        for field in ("rollout_server.online_router.port", "rollout_server.tracking_rollout.port"):
            if dot_get(cfg, field) is MISSING:
                add_issue(issues, "error", f"coding_online_rl missing {field}.")
        external["coding_online_ports"] = {
            "completion": dot_get(cfg, "rollout_server.online_router.port", None),
            "feedback": dot_get(cfg, "rollout_server.tracking_rollout.port", None),
        }
    if workflow == "offline-code-judge":
        external["llm_as_judge_env"] = env_status(["LLMASJUDGE_API_URL", "LLMASJUDGE_API_KEY", "LLMASJUDGE_MODEL"])
        if any(v == "missing" for v in external["llm_as_judge_env"].values()):
            add_issue(issues, "warn", "Offline code reward needs LLMASJUDGE_API_URL, LLMASJUDGE_API_KEY, and LLMASJUDGE_MODEL in the environment.")
    if dot_get(cfg, "agentloop") is not MISSING:
        if dot_get(cfg, "agentloop.toolcall_parser") is MISSING and workflow not in {"wideseek-r1"}:
            add_issue(issues, "warn", "Agentic config has agentloop but no agentloop.toolcall_parser.")
        if dot_get(cfg, "tools") is MISSING:
            add_issue(issues, "warn", "Agentic config has agentloop but no tools block.")
    if workflow == "searchr1":
        addr = dot_get(cfg, "tools.search.server_addr")
        external["search_server"] = stringify(addr)
        if not concrete(addr):
            add_issue(issues, "error", "SearchR1 needs a concrete tools.search.server_addr.")
    if workflow == "rstar2":
        host = dot_get(cfg, "tools.codejudge.host_addr")
        port = dot_get(cfg, "tools.codejudge.host_port")
        external["codejudge"] = {"host": stringify(host), "port": stringify(port)}
        if not concrete(host) or not concrete(port):
            add_issue(issues, "error", "rStar2 needs concrete tools.codejudge.host_addr and host_port.")
        if to_bool(recompute_logprobs) is True:
            add_issue(issues, "warn", "Selected rStar2 configs often set recompute_logprobs: false because down-sampling and inference logic can conflict.")
    if workflow == "wideseek-r1":
        online = to_bool(dot_get(cfg, "tools.online"))
        use_jina = to_bool(dot_get(cfg, "tools.use_jina"))
        if online:
            names = ["SERPER_API_KEY"] + (["JINA_API_KEY"] if use_jina else [])
            external["web_search_env"] = env_status(names)
            if any(v == "missing" for v in external["web_search_env"].values()):
                add_issue(issues, "warn", f"WideSeek online tools need environment keys: {', '.join(names)}.")
        else:
            addr = dot_get(cfg, "tools.search.server_addr")
            external["offline_search_server"] = stringify(addr)
            if not concrete(addr):
                add_issue(issues, "warn", "WideSeek offline mode needs concrete tools.search.server_addr.")
        llm_ip = dot_get(cfg, "agentloop.llm_ip")
        llm_port = dot_get(cfg, "agentloop.llm_port")
        if to_bool(dot_get(cfg, "agentloop.use_llm_judge", True)) and to_bool(dot_get(cfg, "agentloop.use_local_judge")) is not True:
            if not concrete(llm_ip) or not concrete(llm_port):
                add_issue(issues, "warn", "WideSeek external judge needs concrete agentloop.llm_ip and llm_port, or use_local_judge true with a local judge rollout config.")
    data_type = dot_get(cfg, "data.type")
    if data_type == "vlm":
        image_keys = dot_get(cfg, "data.image_keys")
        if not image_keys:
            add_issue(issues, "error", "VLM data config needs non-empty data.image_keys.")
    if workflow in {"sft", "vlm-sft", "sft-or-reward-model"}:
        for field in ("actor.micro_batch_size", "actor.global_batch_size"):
            if dot_get(cfg, field) is MISSING:
                add_issue(issues, "warn", f"SFT/reward training config missing {field}.")
        if dot_get(cfg, "data.train_data_paths") is MISSING or dot_get(cfg, "data.train_data_paths") is None:
            add_issue(issues, "warn", "data.train_data_paths is missing/null; some SFT launchers will run eval-only.")

    # Summarize severity.
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warn_count = sum(1 for i in issues if i["severity"] == "warn")
    summary = {
        "path": str(path),
        "workflow": workflow,
        "task_type": stringify(task_type),
        "components": sorted(components.keys()),
        "actor_backend": stringify(actor_backend),
        "rollout_backend": stringify(rollout_backend),
        "model_type": stringify(dot_get(cfg, "rollout.model.model_type", dot_get(cfg, "actor.model.model_type", MISSING))),
        "algorithm": {
            "adv_type": stringify(adv_type),
            "loss_type": stringify(loss_type),
            "group_size": stringify(group_size),
            "n_minibatches": stringify(dot_get(cfg, "algorithm.n_minibatches")),
            "recompute_logprobs": stringify(recompute_logprobs),
            "return_logprobs": stringify(return_logprobs),
            "sampling_temperature": stringify(dot_get(cfg, "algorithm.sampling_params.temperature")),
        },
        "lengths": {
            "runner.seq_length": stringify(seq_length),
            "data.max_prompt_length": stringify(max_prompt_length),
            "sampling.max_new_tokens": stringify(max_new_tokens),
            "resolved_generation_budget": None if seq_i is None or prompt_i is None else seq_i - prompt_i,
            "resolved_max_new_tokens": max_new_i,
        },
        "data": {
            "type": stringify(data_type),
            "dataset_name": stringify(dot_get(cfg, "data.dataset_name")),
            "prompt_key": stringify(dot_get(cfg, "data.prompt_key")),
            "answer_key": stringify(dot_get(cfg, "data.answer_key")),
            "image_keys": dot_get(cfg, "data.image_keys", []),
            "train_data_paths": stringify(dot_get(cfg, "data.train_data_paths")),
            "val_data_paths": stringify(dot_get(cfg, "data.val_data_paths")),
        },
        "external": external,
        "issue_counts": {"errors": error_count, "warnings": warn_count},
        "issues": issues,
    }
    return summary


def print_text(results: list[dict[str, Any]]) -> None:
    for result in results:
        print(f"== {result['path']}")
        if result.get("parse_error"):
            print(f"PARSE ERROR: {result['parse_error']}")
            continue
        print(f"workflow:        {result['workflow']}")
        print(f"task_type:       {result['task_type']}")
        print(f"components:      {', '.join(result['components']) or '<none>'}")
        print(f"actor backend:   {result['actor_backend']}")
        print(f"rollout backend: {result['rollout_backend']}")
        print(f"model_type:      {result['model_type']}")
        alg = result["algorithm"]
        print(
            "algorithm:      "
            f"adv={alg['adv_type']} loss={alg['loss_type']} group={alg['group_size']} "
            f"minibatches={alg['n_minibatches']} recompute={alg['recompute_logprobs']} "
            f"return_logprobs={alg['return_logprobs']} temp={alg['sampling_temperature']}"
        )
        lengths = result["lengths"]
        print(
            "lengths:        "
            f"seq={lengths['runner.seq_length']} prompt={lengths['data.max_prompt_length']} "
            f"max_new={lengths['sampling.max_new_tokens']} "
            f"budget={lengths['resolved_generation_budget']} resolved_max_new={lengths['resolved_max_new_tokens']}"
        )
        data = result["data"]
        print(
            "data:           "
            f"type={data['type']} dataset={data['dataset_name']} prompt_key={data['prompt_key']} "
            f"answer_key={data['answer_key']} image_keys={stringify(data['image_keys'])}"
        )
        if result["external"]:
            print("external:       " + json.dumps(result["external"], ensure_ascii=False))
        counts = result["issue_counts"]
        print(f"issues:         {counts['errors']} error(s), {counts['warnings']} warning(s)")
        for issue in result["issues"]:
            print(f"  [{issue['severity']}] {issue['message']}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Statically inspect RLinf reasoning/agentic/SFT YAML configs without launching training.",
    )
    parser.add_argument(
        "configs",
        nargs="+",
        help="YAML config file(s) to inspect. Hydra defaults are not composed; pass a fully composed YAML for deepest checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any inspected config has an error-level issue.",
    )
    args = parser.parse_args(argv)

    results = []
    missing_paths = []
    for name in args.configs:
        path = Path(name).expanduser()
        if not path.exists():
            missing_paths.append(str(path))
            results.append(
                {
                    "path": str(path),
                    "parse_error": "file does not exist",
                    "issues": [{"severity": "error", "message": "File does not exist."}],
                    "issue_counts": {"errors": 1, "warnings": 0},
                }
            )
            continue
        results.append(inspect_config(path))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_text(results)

    has_errors = any(
        issue.get("severity") == "error"
        for result in results
        for issue in result.get("issues", [])
    )
    if missing_paths or (args.strict and has_errors):
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
