#!/usr/bin/env python3
"""Safe AReaL dataset/reward/workflow contract checker.

This script performs static-ish contract checks for user-provided sample JSON and
import paths. It never starts AReaL training, launches services, downloads models,
or calls remote providers by default. Importing a user path can still execute that
module's top-level Python code; only pass paths that the user intentionally wants
to inspect.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

STANDARD_RLVR_REWARD_NAMES = {"prompt", "completions", "prompt_ids", "completion_ids"}
MESSAGE_ROLES = {"system", "user", "assistant", "tool", "function", "developer"}


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    hint: str | None = None
    context: str | None = None


class Reporter:
    def __init__(self) -> None:
        self.issues: list[Issue] = []
        self.facts: list[dict[str, Any]] = []

    def add(
        self,
        severity: str,
        code: str,
        message: str,
        *,
        hint: str | None = None,
        context: str | None = None,
    ) -> None:
        self.issues.append(Issue(severity, code, message, hint, context))

    def error(self, code: str, message: str, **kwargs: Any) -> None:
        self.add("error", code, message, **kwargs)

    def warning(self, code: str, message: str, **kwargs: Any) -> None:
        self.add("warning", code, message, **kwargs)

    def info(self, code: str, message: str, **kwargs: Any) -> None:
        self.add("info", code, message, **kwargs)

    def fact(self, **kwargs: Any) -> None:
        self.facts.append(kwargs)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == "warning" for issue in self.issues)


def import_from_string(module_path: str) -> Any:
    if not module_path or not isinstance(module_path, str):
        raise ValueError(
            f"Invalid module path {module_path!r}; expected 'module.path.ObjectName'."
        )
    parts = module_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid module path {module_path!r}; expected 'module.path.ObjectName'."
        )
    module_name, object_name = parts
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def load_rollout_base() -> type | None:
    try:
        from areal.api.workflow_api import RolloutWorkflow

        return RolloutWorkflow
    except Exception:
        return None


def safe_signature(obj: Any) -> inspect.Signature | None:
    try:
        return inspect.signature(obj)
    except (TypeError, ValueError):
        return None


def required_constructor_params(cls: type) -> list[str]:
    sig = safe_signature(cls)
    if sig is None:
        return []
    required: list[str] = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if param.default is param.empty:
            required.append(name)
    return required


def is_async_method(obj: Any, name: str) -> bool:
    member = getattr(obj, name, None)
    return callable(member) and inspect.iscoroutinefunction(member)


def validate_agent_like(obj: Any, path: str, reporter: Reporter, *, context: str) -> None:
    run = getattr(obj, "run", None)
    if run is None or not callable(run):
        reporter.error(
            "agent.run.missing",
            f"{path} is not a RolloutWorkflow and has no callable run method.",
            hint="Agent workflows need async def run(self, data, **extra_kwargs).",
            context=context,
        )
        return

    if not inspect.iscoroutinefunction(run):
        reporter.error(
            "agent.run.not_async",
            f"{path}.run is not an async function.",
            hint="Use async def run(...), or wrap sync framework code in rollout.agent.mode=subproc while keeping the method async.",
            context=context,
        )
    else:
        reporter.fact(path=path, kind="agent_workflow", run="async")

    sig = safe_signature(run)
    if sig is None:
        reporter.warning(
            "agent.run.signature_unknown",
            f"Could not inspect {path}.run signature.",
            context=context,
        )
        return

    params = [p for p in sig.parameters.values() if p.name != "self"]
    if not params:
        reporter.error(
            "agent.run.no_data_param",
            f"{path}.run has no data parameter.",
            hint="Expected async def run(self, data: dict, **extra_kwargs).",
            context=context,
        )
    else:
        first = params[0]
        if first.kind not in (first.POSITIONAL_ONLY, first.POSITIONAL_OR_KEYWORD):
            reporter.warning(
                "agent.run.data_unusual",
                f"First non-self parameter of {path}.run is {first.kind}, not positional data.",
                hint="AReaL calls agent.run(data, **extra_kwargs).",
                context=context,
            )

    has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params)
    if not has_var_kw:
        reporter.warning(
            "agent.run.no_extra_kwargs",
            f"{path}.run does not accept **extra_kwargs.",
            hint="Proxy mode injects base_url, api_key, and http_client through extra_kwargs.",
            context=context,
        )

    if isinstance(obj, type):
        required = required_constructor_params(obj)
        if required:
            reporter.info(
                "agent.constructor.requires_kwargs",
                f"{path} constructor requires arguments: {', '.join(required)}.",
                hint="Pass matching workflow_kwargs when using this class in trainer code.",
                context=context,
            )


def validate_workflow_path(path: str, reporter: Reporter) -> None:
    context = f"workflow:{path}"
    try:
        obj = import_from_string(path)
    except Exception as exc:  # noqa: BLE001 - report user import error cleanly
        reporter.error(
            "workflow.import_failed",
            f"Failed to import workflow path {path!r}: {exc}",
            hint="Ensure the module is installed/on PYTHONPATH and has no unsafe top-level side effects.",
            context=context,
        )
        return

    rollout_base = load_rollout_base()
    is_rollout = False
    if rollout_base is not None:
        try:
            if isinstance(obj, type):
                is_rollout = issubclass(obj, rollout_base)
            else:
                is_rollout = isinstance(obj, rollout_base)
        except TypeError:
            is_rollout = False

    if is_rollout or is_async_method(obj, "arun_episode"):
        if not is_async_method(obj, "arun_episode"):
            reporter.error(
                "workflow.arun_episode.not_async",
                f"{path}.arun_episode is missing or not async.",
                hint="RolloutWorkflow subclasses must implement async def arun_episode(self, engine, data).",
                context=context,
            )
        else:
            reporter.fact(path=path, kind="rollout_workflow", arun_episode="async")
        if isinstance(obj, type):
            required = required_constructor_params(obj)
            if required:
                reporter.info(
                    "workflow.constructor.requires_kwargs",
                    f"{path} constructor requires arguments: {', '.join(required)}.",
                    hint="Pass matching workflow_kwargs when using this class in trainer code.",
                    context=context,
                )
        return

    reporter.info(
        "workflow.agent_like",
        f"{path} does not resolve to a RolloutWorkflow; AReaL will treat it as an agent-like workflow requiring proxy workers.",
        hint="This is valid only if the object/class has async run(data, **extra_kwargs).",
        context=context,
    )
    validate_agent_like(obj, path, reporter, context=context)


def positional_capacity(sig: inspect.Signature) -> tuple[int, bool]:
    params = list(sig.parameters.values())
    positional = [
        p
        for p in params
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    has_varargs = any(p.kind == p.VAR_POSITIONAL for p in params)
    return len(positional), has_varargs


def validate_reward_path(
    path: str,
    reporter: Reporter,
    *,
    records: list[dict[str, Any]],
    mode: str,
    execute: bool,
    prompt: str,
    completion: str,
    prompt_ids: list[int],
    completion_ids: list[int],
) -> None:
    context = f"reward:{path}"
    try:
        obj = import_from_string(path)
    except Exception as exc:  # noqa: BLE001
        reporter.error(
            "reward.import_failed",
            f"Failed to import reward path {path!r}: {exc}",
            hint="Use a fully qualified module path and install dependencies in every worker environment.",
            context=context,
        )
        return

    if not callable(obj):
        reporter.error(
            "reward.not_callable",
            f"Imported reward object {path!r} is not callable.",
            context=context,
        )
        return

    reporter.fact(path=path, kind="reward", callable=True)

    coroutine_severity = "error" if mode in {"rlvr", "vision-rlvr"} else "warning"
    if inspect.iscoroutinefunction(obj):
        reporter.add(
            coroutine_severity,
            "reward.async_function",
            f"{path} is async; stock RLVR workflows expect a synchronous reward for AsyncRewardWrapper.",
            hint="Use a sync module-level wrapper or await the reward from a custom RolloutWorkflow.",
            context=context,
        )

    sig = safe_signature(obj)
    if sig is None:
        reporter.warning(
            "reward.signature_unknown",
            f"Could not inspect reward signature for {path}.",
            context=context,
        )
    else:
        n_positional, has_varargs = positional_capacity(sig)
        if not has_varargs and n_positional < 4 and mode in {"rlvr", "vision-rlvr"}:
            reporter.error(
                "reward.too_few_positional_args",
                f"{path} accepts only {n_positional} positional parameters, but stock RLVR passes prompt, completions, prompt_ids, completion_ids.",
                hint="Use def reward_fn(prompt, completions, prompt_ids, completion_ids, **kwargs) -> float.",
                context=context,
            )

        params = list(sig.parameters.values())
        has_varkw = any(p.kind == p.VAR_KEYWORD for p in params)
        named_params = {p.name for p in params}
        sample = records[0] if records else {}

        if sample:
            collisions = STANDARD_RLVR_REWARD_NAMES.intersection(sample.keys())
            if collisions:
                reporter.warning(
                    "reward.sample_key_collision",
                    "Sample contains keys that stock RLVR also passes positionally: "
                    + ", ".join(sorted(collisions)),
                    hint="Rename dataset fields or verify the reward accepts *args/**kwargs without duplicate parameter names.",
                    context=context,
                )

            if not has_varkw:
                unsupported = set(sample.keys()) - named_params
                if unsupported:
                    reporter.error(
                        "reward.unaccepted_sample_kwargs",
                        f"{path} has no **kwargs and does not accept sample keys: {', '.join(sorted(unsupported))}.",
                        hint="AReaL passes all dataset row fields into stock RLVR rewards as keyword arguments.",
                        context=context,
                    )

            required_missing: list[str] = []
            consumed_positional = 0
            for param in params:
                if param.kind == param.VAR_POSITIONAL:
                    consumed_positional = 4
                    continue
                if param.kind == param.VAR_KEYWORD:
                    continue
                if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                    consumed_positional += 1
                    if consumed_positional <= 4:
                        continue
                if param.default is param.empty and param.name not in sample:
                    required_missing.append(param.name)
            if required_missing:
                reporter.error(
                    "reward.required_kwargs_missing",
                    f"Sample does not provide required reward parameters: {', '.join(required_missing)}.",
                    hint="Keep those fields in the dataset row or add defaults.",
                    context=context,
                )

    if execute:
        sample = records[0] if records else {}
        try:
            result = obj(prompt, completion, prompt_ids, completion_ids, **sample)
            if asyncio.iscoroutine(result):
                reporter.error(
                    "reward.returned_coroutine",
                    f"{path} returned a coroutine object when called like stock RLVR.",
                    hint="Await it in a custom workflow or make the reward synchronous.",
                    context=context,
                )
            elif isinstance(result, bool) or not isinstance(result, (int, float)):
                reporter.error(
                    "reward.return_not_scalar",
                    f"{path} returned {type(result).__name__}, not a numeric scalar.",
                    hint="Stock RLVR reward functions should return float.",
                    context=context,
                )
            elif not math.isfinite(float(result)):
                reporter.error(
                    "reward.return_not_finite",
                    f"{path} returned non-finite reward {result!r}.",
                    context=context,
                )
            else:
                reporter.fact(path=path, kind="reward_execution", result=float(result))
        except Exception as exc:  # noqa: BLE001
            reporter.error(
                "reward.execution_failed",
                f"Executing {path} with stock RLVR arguments failed: {type(exc).__name__}: {exc}",
                hint="This reproduces the call shape reward(prompt, completions, prompt_ids, completion_ids, **sample).",
                context=context,
            )


def load_records(sample_json: str, reporter: Reporter) -> list[dict[str, Any]]:
    context = f"sample:{sample_json}"
    try:
        text = sys.stdin.read() if sample_json == "-" else Path(sample_json).read_text()
    except Exception as exc:  # noqa: BLE001
        reporter.error("sample.read_failed", f"Could not read sample JSON: {exc}", context=context)
        return []

    stripped = text.lstrip()
    if not stripped:
        reporter.error("sample.empty", "Sample JSON is empty.", context=context)
        return []

    data: Any
    records: list[Any]
    try:
        if stripped[0] in "[{":
            data = json.loads(text)
            if isinstance(data, dict):
                if isinstance(data.get("records"), list):
                    records = data["records"]
                else:
                    records = [data]
            elif isinstance(data, list):
                records = data
            else:
                reporter.error(
                    "sample.top_level_invalid",
                    f"Top-level JSON must be an object, list, or object with records; got {type(data).__name__}.",
                    context=context,
                )
                return []
        else:
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
    except Exception as exc:  # noqa: BLE001
        reporter.error("sample.parse_failed", f"Could not parse sample JSON/JSONL: {exc}", context=context)
        return []

    dict_records: list[dict[str, Any]] = []
    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            reporter.error(
                "sample.record_not_object",
                f"Record {idx} is {type(item).__name__}, not an object.",
                context=context,
            )
            continue
        dict_records.append(item)
    reporter.fact(kind="sample", path=sample_json, records=len(dict_records))
    return dict_records


def is_int_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in value)


def validate_token_pair(
    record: dict[str, Any],
    left: str,
    right: str,
    reporter: Reporter,
    *,
    context: str,
) -> None:
    if left not in record:
        reporter.error("sample.key_missing", f"Missing key {left!r}.", context=context)
        return
    if right not in record:
        reporter.error("sample.key_missing", f"Missing key {right!r}.", context=context)
        return
    if not is_int_list(record[left]):
        reporter.error("sample.tokens_invalid", f"{left!r} must be a list of integers.", context=context)
    if not is_int_list(record[right]):
        reporter.error("sample.tokens_invalid", f"{right!r} must be a list of integers.", context=context)


def validate_same_length(
    record: dict[str, Any],
    left: str,
    right: str,
    reporter: Reporter,
    *,
    context: str,
) -> None:
    if left in record and right in record and isinstance(record[left], list) and isinstance(record[right], list):
        if len(record[left]) != len(record[right]):
            reporter.error(
                "sample.length_mismatch",
                f"{left!r} length {len(record[left])} != {right!r} length {len(record[right])}.",
                context=context,
            )


def validate_message_content(
    content: Any,
    reporter: Reporter,
    *,
    context: str,
    allow_empty_image_url: bool,
) -> None:
    if isinstance(content, str):
        return
    if not isinstance(content, list):
        reporter.error(
            "messages.content_invalid",
            f"Message content must be a string or list of content parts, got {type(content).__name__}.",
            context=context,
        )
        return
    for part_idx, part in enumerate(content):
        pctx = f"{context}.content[{part_idx}]"
        if not isinstance(part, dict):
            reporter.error("messages.part_invalid", "Content part must be an object.", context=pctx)
            continue
        ptype = part.get("type")
        if ptype == "text":
            if not isinstance(part.get("text"), str):
                reporter.error("messages.text_missing", "Text content part requires string field 'text'.", context=pctx)
        elif ptype == "image_url":
            image_url = part.get("image_url")
            if not isinstance(image_url, dict):
                reporter.error("messages.image_url_invalid", "image_url part requires object field 'image_url'.", context=pctx)
                continue
            url = image_url.get("url")
            if not isinstance(url, str):
                reporter.error("messages.image_url_missing", "image_url.url must be a string.", context=pctx)
            elif url == "" and not allow_empty_image_url:
                reporter.error(
                    "messages.image_url_empty",
                    "Proxy OpenAI VLM calls cannot use an empty image_url.url.",
                    hint="Use a real HTTP(S) URL or data:image/...;base64,... URI. Empty placeholders are only for direct VisionRLVRWorkflow rows.",
                    context=pctx,
                )
        else:
            reporter.warning(
                "messages.part_unknown_type",
                f"Unknown content part type {ptype!r}.",
                hint="Common types are 'text' and 'image_url'.",
                context=pctx,
            )


def validate_messages(
    value: Any,
    reporter: Reporter,
    *,
    context: str,
    allow_string: bool,
    allow_empty_image_url: bool,
) -> None:
    if isinstance(value, str):
        if not allow_string:
            reporter.warning(
                "messages.string_unusual",
                "messages is a string; stock text RLVR/agent prompts usually use a list of chat messages.",
                hint="A string is normal for direct VisionRLVRWorkflow after applying a processor chat template.",
                context=context,
            )
        return

    if not isinstance(value, list):
        reporter.error("messages.not_list", f"messages must be a list, got {type(value).__name__}.", context=context)
        return
    if not value:
        reporter.error("messages.empty", "messages must not be empty.", context=context)
        return
    for idx, msg in enumerate(value):
        mctx = f"{context}[{idx}]"
        if not isinstance(msg, dict):
            reporter.error("messages.item_not_object", "Each message must be an object.", context=mctx)
            continue
        role = msg.get("role")
        if role not in MESSAGE_ROLES:
            reporter.warning(
                "messages.role_unknown",
                f"Message role {role!r} is not one of {sorted(MESSAGE_ROLES)}.",
                context=mctx,
            )
        if "content" not in msg and "tool_calls" not in msg:
            reporter.warning(
                "messages.no_content",
                "Message has neither content nor tool_calls.",
                context=mctx,
            )
        if "content" in msg:
            validate_message_content(
                msg["content"],
                reporter,
                context=mctx,
                allow_empty_image_url=allow_empty_image_url,
            )
        if role == "tool" and "tool_call_id" not in msg:
            reporter.warning(
                "messages.tool_missing_call_id",
                "Tool messages normally include tool_call_id.",
                context=mctx,
            )


def validate_record(
    record: dict[str, Any],
    idx: int,
    mode: str,
    required_keys: list[str],
    reporter: Reporter,
) -> None:
    context = f"record[{idx}]"
    for key in required_keys:
        if key not in record:
            reporter.error("sample.required_key_missing", f"Missing required key {key!r}.", context=context)

    if mode == "generic":
        return

    if mode == "rlvr":
        if "messages" not in record:
            reporter.error("sample.key_missing", "RLVR samples require 'messages'.", context=context)
        else:
            validate_messages(record["messages"], reporter, context=f"{context}.messages", allow_string=False, allow_empty_image_url=False)
        if "answer" not in record:
            reporter.warning("sample.answer_missing", "No 'answer' key found; many RLVR rewards require it.", context=context)
        return

    if mode == "vision-rlvr":
        if "messages" not in record:
            reporter.error("sample.key_missing", "VisionRLVR samples require 'messages'.", context=context)
        else:
            validate_messages(record["messages"], reporter, context=f"{context}.messages", allow_string=True, allow_empty_image_url=True)
        images = record.get("images")
        if not isinstance(images, list) or not images:
            reporter.error("sample.images_invalid", "VisionRLVR samples require non-empty list key 'images'.", context=context)
        if "messages_chat" in record:
            validate_messages(record["messages_chat"], reporter, context=f"{context}.messages_chat", allow_string=False, allow_empty_image_url=True)
        if "answer" not in record:
            reporter.warning("sample.answer_missing", "No 'answer' key found; many VLM rewards require it.", context=context)
        return

    if mode == "agent":
        if "messages" not in record and "messages_chat" not in record:
            reporter.error("sample.key_missing", "Agent samples usually require 'messages' or 'messages_chat'.", context=context)
        if "messages" in record:
            validate_messages(record["messages"], reporter, context=f"{context}.messages", allow_string=True, allow_empty_image_url=False)
        if "messages_chat" in record:
            validate_messages(record["messages_chat"], reporter, context=f"{context}.messages_chat", allow_string=False, allow_empty_image_url=False)
        return

    if mode == "sft":
        validate_token_pair(record, "input_ids", "loss_mask", reporter, context=context)
        validate_same_length(record, "input_ids", "loss_mask", reporter, context=context)
        return

    if mode == "rw":
        validate_token_pair(record, "chosen_ids", "rejected_ids", reporter, context=context)
        return

    if mode == "dpo":
        validate_token_pair(record, "chosen_ids", "rejected_ids", reporter, context=context)
        validate_token_pair(record, "chosen_loss_mask", "rejected_loss_mask", reporter, context=context)
        validate_same_length(record, "chosen_ids", "chosen_loss_mask", reporter, context=context)
        validate_same_length(record, "rejected_ids", "rejected_loss_mask", reporter, context=context)
        return


def split_required(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                result.append(item)
    return result


def parse_int_list(value: str) -> list[int]:
    if value.strip() == "":
        return []
    try:
        parsed = json.loads(value)
        if is_int_list(parsed):
            return parsed
    except json.JSONDecodeError:
        pass
    try:
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected JSON int list or comma-separated ints, got {value!r}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate AReaL dataset samples, reward functions, RolloutWorkflow imports, and proxy-agent workflow imports without starting training/services.",
        epilog=(
            "Examples:\n"
            "  python scripts/check_workflow_contract.py --sample-json sample.json --mode rlvr --require answer\n"
            "  python scripts/check_workflow_contract.py --workflow my_pkg.agent.MyAgent --mode agent\n"
            "  python scripts/check_workflow_contract.py --reward my_pkg.reward.reward_fn --sample-json sample.json --mode rlvr --execute-reward"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--workflow", action="append", default=[], help="Dotted import path to a RolloutWorkflow or agent-like workflow class/instance. May be repeated.")
    parser.add_argument("--reward", action="append", default=[], help="Dotted import path to a reward function. May be repeated.")
    parser.add_argument("--sample-json", help="JSON/JSONL sample file to validate, or '-' for stdin.")
    parser.add_argument("--mode", choices=["generic", "rlvr", "vision-rlvr", "agent", "sft", "rw", "dpo"], default="generic", help="Sample contract to validate.")
    parser.add_argument("--require", action="append", help="Additional required sample key. May be repeated or comma-separated.")
    parser.add_argument("--max-samples", type=int, default=5, help="Maximum records to validate from sample JSON/JSONL.")
    parser.add_argument("--execute-reward", action="store_true", help="Explicitly call reward(prompt, completion, prompt_ids, completion_ids, **sample). This executes user code.")
    parser.add_argument("--prompt", default="", help="Prompt string used with --execute-reward.")
    parser.add_argument("--completion", default="", help="Completion string used with --execute-reward.")
    parser.add_argument("--prompt-ids", type=parse_int_list, default=[], help="Prompt token ids for --execute-reward, as JSON list or comma-separated ints.")
    parser.add_argument("--completion-ids", type=parse_int_list, default=[], help="Completion token ids for --execute-reward, as JSON list or comma-separated ints.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser


def print_text_report(reporter: Reporter, *, strict: bool) -> None:
    print("AReaL workflow contract check")
    if reporter.facts:
        print("\nFacts:")
        for fact in reporter.facts:
            print("  - " + ", ".join(f"{k}={v!r}" for k, v in fact.items()))
    if reporter.issues:
        print("\nIssues:")
        for issue in reporter.issues:
            loc = f" [{issue.context}]" if issue.context else ""
            print(f"  - {issue.severity.upper()} {issue.code}{loc}: {issue.message}")
            if issue.hint:
                print(f"    hint: {issue.hint}")
    else:
        print("\nNo issues found.")
    if reporter.has_errors:
        print("\nResult: FAILED (errors found)")
    elif strict and reporter.has_warnings:
        print("\nResult: FAILED (--strict treats warnings as failures)")
    else:
        print("\nResult: OK")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reporter = Reporter()

    if args.max_samples <= 0:
        reporter.error("args.max_samples_invalid", "--max-samples must be positive.")

    records: list[dict[str, Any]] = []
    if args.sample_json:
        records = load_records(args.sample_json, reporter)
        required_keys = split_required(args.require)
        for idx, record in enumerate(records[: max(args.max_samples, 0)]):
            validate_record(record, idx, args.mode, required_keys, reporter)
    elif args.require:
        reporter.warning("sample.require_without_sample", "--require was provided without --sample-json.")

    for workflow_path in args.workflow:
        validate_workflow_path(workflow_path, reporter)

    for reward_path in args.reward:
        validate_reward_path(
            reward_path,
            reporter,
            records=records,
            mode=args.mode,
            execute=args.execute_reward,
            prompt=args.prompt,
            completion=args.completion,
            prompt_ids=args.prompt_ids,
            completion_ids=args.completion_ids,
        )

    if not (args.sample_json or args.workflow or args.reward):
        reporter.info(
            "no_inputs",
            "No checks requested. Provide --sample-json, --workflow, or --reward. Use --help for examples.",
        )

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not reporter.has_errors and not (args.strict and reporter.has_warnings),
                    "strict": args.strict,
                    "facts": reporter.facts,
                    "issues": [asdict(issue) for issue in reporter.issues],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text_report(reporter, strict=args.strict)

    if reporter.has_errors or (args.strict and reporter.has_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
