#!/usr/bin/env python3
"""Safe LLM Foundry data-preparation smoke probe.

This helper is intentionally read-only by default. It inspects importability and
function signatures, checks whether the `llmfoundry` console script is on PATH,
and optionally validates a tiny local JSON/JSONL fixture. It does not download
models or datasets, query Databricks, contact object stores, or write MDS data.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TARGETS = [
    ('StreamingTextDataset', 'llmfoundry.data.text_data', 'StreamingTextDataset'),
    ('StreamingFinetuningDataset', 'llmfoundry.data.finetuning.tasks', 'StreamingFinetuningDataset'),
    ('build_text_dataloader', 'llmfoundry.data.text_data', 'build_text_dataloader'),
    ('build_finetuning_dataloader', 'llmfoundry.data.finetuning.dataloader', 'build_finetuning_dataloader'),
    ('convert_dataset_hf_from_args', 'llmfoundry.command_utils.data_prep.convert_dataset_hf', 'convert_dataset_hf_from_args'),
    ('convert_dataset_json_from_args', 'llmfoundry.command_utils.data_prep.convert_dataset_json', 'convert_dataset_json_from_args'),
    ('convert_finetuning_dataset_from_args', 'llmfoundry.command_utils.data_prep.convert_finetuning_dataset', 'convert_finetuning_dataset_from_args'),
    ('convert_text_to_mds_from_args', 'llmfoundry.command_utils.data_prep.convert_text_to_mds', 'convert_text_to_mds_from_args'),
    ('convert_delta_to_json_from_args', 'llmfoundry.command_utils.data_prep.convert_delta_to_json', 'convert_delta_to_json_from_args'),
    ('data_prep_cli_app', 'llmfoundry.cli.data_prep_cli', 'app'),
]

CORE_DEPENDENCIES = [
    'llmfoundry',
    'torch',
    'transformers',
    'datasets',
    'streaming',
    'composer',
    'typer',
]

DELTA_DEPENDENCIES = [
    'databricks.sdk',
    'databricks.sql',
    'databricks.connect',
    'pyspark',
    'pyarrow',
    'pandas',
    'requests',
    'lz4.frame',
]

CHAT_ROLES = {'user', 'assistant', 'system', 'tool'}


def module_available(name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, AttributeError, ValueError) as exc:
        return {
            'module': name,
            'available': False,
            'origin': None,
            'error': f'{type(exc).__name__}: {exc}',
        }
    return {
        'module': name,
        'available': spec is not None,
        'origin': getattr(spec, 'origin', None) if spec is not None else None,
    }


def inspect_target(label: str, module_name: str, attr_name: str) -> dict[str, Any]:
    item: dict[str, Any] = {
        'label': label,
        'module': module_name,
        'attribute': attr_name,
        'ok': False,
    }
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr_name)
        item['ok'] = True
        try:
            item['signature'] = str(inspect.signature(obj))
        except (TypeError, ValueError):
            item['signature'] = '<no inspectable signature>'
        item['type'] = type(obj).__name__
    except Exception as exc:  # noqa: BLE001 - probe should report all import failures.
        item['error_type'] = type(exc).__name__
        item['error'] = str(exc) or repr(exc)
    return item


def load_json_records(path: Path, max_lines: int) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    if not path.exists():
        return [], [f'fixture does not exist: {path}']
    if not path.is_file():
        return [], [f'fixture is not a file: {path}']

    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        return [], [f'fixture is not valid UTF-8 text: {exc}']

    stripped = text.lstrip()
    if not stripped:
        return [], ['fixture is empty']

    if path.suffix.lower() == '.json' and stripped[0] in '[{':
        try:
            obj = json.loads(text)
            if isinstance(obj, list):
                iterable = obj[:max_lines]
            else:
                iterable = [obj]
            for idx, record in enumerate(iterable, start=1):
                if isinstance(record, dict):
                    records.append(record)
                else:
                    errors.append(f'record {idx}: expected JSON object, got {type(record).__name__}')
            return records, errors
        except json.JSONDecodeError:
            # Fall back to JSONL parsing below; a .json extension is not authoritative.
            pass

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no > max_lines:
            break
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f'line {line_no}: invalid JSON: {exc.msg}')
            continue
        if not isinstance(record, dict):
            errors.append(f'line {line_no}: expected JSON object, got {type(record).__name__}')
            continue
        records.append(record)
    return records, errors


def parse_negative_passages(value: Any, where: str, errors: list[str]) -> None:
    if value is None:
        return
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            errors.append(f'{where}: negative_passages string must be a JSON-encoded list')
            return
    if not isinstance(parsed, list):
        errors.append(f'{where}: negative_passages must be a list or JSON-encoded list string')
        return
    for i, item in enumerate(parsed):
        if not isinstance(item, str):
            errors.append(f'{where}: negative_passages[{i}] must be a string')


def check_pretraining(record: dict[str, Any], where: str, strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if 'text' not in record:
        errors.append(f'{where}: missing required key "text"')
    elif not isinstance(record['text'], str):
        errors.append(f'{where}: "text" must be a string, got {type(record["text"]).__name__}')
    elif record['text'] == '':
        warnings.append(f'{where}: "text" is empty')
    extra = set(record) - {'text'}
    if extra:
        message = f'{where}: pretraining converter ignores/exposes unexpected keys {sorted(extra)}; safest schema has only "text"'
        (errors if strict else warnings).append(message)
    return errors, warnings


def is_prompt_response(record: dict[str, Any]) -> bool:
    return 'prompt' in record and 'response' in record


def check_prompt_response(record: dict[str, Any], where: str, strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for key in ('prompt', 'response'):
        if key not in record:
            errors.append(f'{where}: missing required key "{key}"')
        elif not isinstance(record[key], str):
            errors.append(f'{where}: "{key}" must be a string, got {type(record[key]).__name__}')
        elif record[key] == '':
            warnings.append(f'{where}: "{key}" is empty and may be dropped or rejected')
    extra = set(record) - {'prompt', 'response'}
    if extra:
        message = f'{where}: extra keys {sorted(extra)} should be removed by a preprocessing function before LLM Foundry formatting'
        (errors if strict else warnings).append(message)
    return errors, warnings


def check_chat(record: dict[str, Any], where: str, strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if 'messages' not in record:
        return [f'{where}: missing required key "messages"'], warnings
    messages = record['messages']
    if not isinstance(messages, list):
        return [f'{where}: "messages" must be a list'], warnings
    if len(messages) <= 1:
        errors.append(f'{where}: "messages" should contain at least user and assistant turns')
    previous_role: str | None = None
    for idx, message in enumerate(messages):
        msg_where = f'{where}.messages[{idx}]'
        if not isinstance(message, dict):
            errors.append(f'{msg_where}: message must be an object')
            continue
        msg_keys = set(message)
        required = {'role', 'content'}
        missing = required - msg_keys
        if missing:
            errors.append(f'{msg_where}: missing keys {sorted(missing)}')
        extra = msg_keys - required
        if extra:
            target = errors if strict else warnings
            target.append(f'{msg_where}: extra keys {sorted(extra)} are not accepted by the strict chat formatter')
        role = message.get('role')
        if not isinstance(role, str):
            errors.append(f'{msg_where}: role must be a string')
        elif role not in CHAT_ROLES:
            errors.append(f'{msg_where}: invalid role {role!r}; expected one of {sorted(CHAT_ROLES)}')
        elif previous_role == role:
            target = errors if strict else warnings
            target.append(f'{msg_where}: consecutive repeated role {role!r}')
        previous_role = role if isinstance(role, str) else previous_role
        content = message.get('content')
        if not isinstance(content, (str, list)):
            errors.append(f'{msg_where}: content must be a string or list, got {type(content).__name__}')
        elif content == '':
            warnings.append(f'{msg_where}: content is empty')
    if messages:
        last = messages[-1]
        if isinstance(last, dict) and last.get('role') != 'assistant':
            errors.append(f'{where}: final chat role must be "assistant"')
    extra_record_keys = set(record) - {'messages'}
    if extra_record_keys:
        target = errors if strict else warnings
        target.append(f'{where}: extra top-level keys {sorted(extra_record_keys)} should be removed before formatting')
    return errors, warnings


def check_contrastive(record: dict[str, Any], where: str, strict: bool) -> tuple[list[str], list[str]]:
    del strict
    errors: list[str] = []
    warnings: list[str] = []
    has_pair = any(k.startswith('text_a') for k in record) and any(k.startswith('text_b') for k in record)
    has_multi = 'query_text' in record and 'positive_passage' in record
    if has_pair:
        for prefix in ('text_a', 'text_b'):
            keys = [k for k in record if k.startswith(prefix)]
            for key in keys:
                if not isinstance(record[key], str):
                    errors.append(f'{where}: {key} must be a string')
        return errors, warnings
    if has_multi:
        for key in ('query_text', 'positive_passage'):
            if not isinstance(record[key], str):
                errors.append(f'{where}: {key} must be a string')
            elif record[key] == '':
                warnings.append(f'{where}: {key} is empty')
        parse_negative_passages(record.get('negative_passages'), where, errors)
        return errors, warnings
    errors.append(f'{where}: contrastive record must contain text_a*/text_b* or query_text/positive_passage')
    return errors, warnings


def validate_records(records: list[dict[str, Any]], schema: str, strict: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    detected = Counter()
    for idx, record in enumerate(records, start=1):
        where = f'record {idx}'
        if schema == 'pretraining':
            e, w = check_pretraining(record, where, strict)
            detected['pretraining'] += int(not e)
        elif schema == 'prompt_response':
            e, w = check_prompt_response(record, where, strict)
            detected['prompt_response'] += int(not e)
        elif schema == 'chat':
            e, w = check_chat(record, where, strict)
            detected['chat'] += int(not e)
        elif schema == 'sft':
            if is_prompt_response(record):
                e, w = check_prompt_response(record, where, strict)
                detected['prompt_response'] += int(not e)
            else:
                e, w = check_chat(record, where, strict)
                detected['chat'] += int(not e)
        elif schema == 'contrastive':
            e, w = check_contrastive(record, where, strict)
            detected['contrastive'] += int(not e)
        elif schema == 'auto':
            candidates: list[tuple[str, list[str], list[str]]] = []
            for name, fn in [
                ('pretraining', check_pretraining),
                ('prompt_response', check_prompt_response),
                ('chat', check_chat),
                ('contrastive', check_contrastive),
            ]:
                e, w = fn(record, where, strict=False)
                if not e:
                    candidates.append((name, e, w))
            if not candidates:
                e, w = [f'{where}: did not match pretraining, SFT, chat, or contrastive schemas'], []
            else:
                name, e, w = candidates[0]
                detected[name] += 1
                if len(candidates) > 1:
                    w.append(f'{where}: matched multiple schemas {[c[0] for c in candidates]}; choose --schema explicitly')
        else:  # defensive; argparse enforces choices.
            e, w = [f'unknown schema: {schema}'], []
        errors.extend(e)
        warnings.extend(w)
    return {
        'records_checked': len(records),
        'detected': dict(detected),
        'warnings': warnings,
        'errors': errors,
        'ok': not errors,
    }


def print_human(report: dict[str, Any]) -> None:
    print('LLM Foundry data-prep smoke probe')
    print(f'python: {sys.executable}')
    if 'cli' in report:
        cli = report['cli']
        print(f"llmfoundry console script: {cli.get('path') or 'not found on PATH'}")
    print('\nDependencies:')
    for dep in report['dependencies']:
        status = 'OK' if dep['available'] else 'MISSING'
        print(f"  {status:7} {dep['module']}")
    print('\nSignatures/imports:')
    for target in report['targets']:
        if target['ok']:
            print(f"  OK      {target['label']}{target.get('signature', '')}")
        else:
            print(f"  MISSING {target['label']} ({target.get('error_type')}: {target.get('error')})")
    if 'fixture' in report:
        fixture = report['fixture']
        print('\nFixture validation:')
        print(f"  path: {fixture['path']}")
        print(f"  schema: {fixture['schema']}")
        print(f"  records checked: {fixture['result'].get('records_checked', 0)}")
        print(f"  detected: {fixture['result'].get('detected', {})}")
        for warning in fixture['result'].get('warnings', []):
            print(f'  WARNING {warning}')
        for error in fixture['result'].get('errors', []):
            print(f'  ERROR   {error}')
        print(f"  ok: {fixture['result'].get('ok', False)}")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    deps = [module_available(name) for name in CORE_DEPENDENCIES]
    if args.include_delta_deps:
        deps.extend(module_available(name) for name in DELTA_DEPENDENCIES)
    report: dict[str, Any] = {
        'python': sys.executable,
        'dependencies': deps,
        'targets': [inspect_target(*target) for target in TARGETS],
    }
    if args.check_cli:
        report['cli'] = {'path': shutil.which('llmfoundry')}
    if args.fixture:
        fixture_path = Path(args.fixture).expanduser().resolve()
        records, load_errors = load_json_records(fixture_path, args.max_lines)
        result = validate_records(records, args.schema, args.strict) if records else {
            'records_checked': 0,
            'detected': {},
            'warnings': [],
            'errors': [],
            'ok': False,
        }
        result['errors'] = load_errors + result.get('errors', [])
        result['ok'] = not result['errors']
        report['fixture'] = {
            'path': str(fixture_path),
            'schema': args.schema,
            'strict': args.strict,
            'max_lines': args.max_lines,
            'result': result,
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Read-only LLM Foundry data-prep import/signature and JSONL schema probe.',
    )
    parser.add_argument('--fixture', help='Optional local JSON/JSONL fixture to validate. No files are written.')
    parser.add_argument(
        '--schema',
        choices=['auto', 'pretraining', 'sft', 'prompt_response', 'chat', 'contrastive'],
        default='auto',
        help='Expected fixture schema. sft accepts prompt_response or chat.',
    )
    parser.add_argument('--max-lines', type=int, default=1000, help='Maximum JSONL lines or JSON list records to inspect.')
    parser.add_argument('--strict', action='store_true', help='Treat extra keys and repeated chat roles as errors.')
    parser.add_argument('--check-cli', action='store_true', help='Report whether the llmfoundry console script is on PATH.')
    parser.add_argument('--include-delta-deps', action='store_true', help='Also check optional Databricks/Delta dependency modules.')
    parser.add_argument('--dump-json', action='store_true', help='Emit machine-readable JSON instead of human text.')
    parser.add_argument('--fail-on-missing', action='store_true', help='Exit nonzero if any target import/signature probe fails.')
    args = parser.parse_args(argv)

    if args.max_lines <= 0:
        parser.error('--max-lines must be positive')

    report = build_report(args)
    if args.dump_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    fixture_bad = 'fixture' in report and not report['fixture']['result']['ok']
    missing_bad = args.fail_on_missing and any(not target['ok'] for target in report['targets'])
    return 1 if fixture_bad or missing_bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
