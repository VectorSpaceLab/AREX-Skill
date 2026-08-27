#!/usr/bin/env python3
"""Offline smoke check for Sparrow-style JSON example schemas.

This mirrors the public behavior documented in the generated skill: a JSON
example query defines required fields and simple value types, then a candidate
JSON response is checked against that shape. No Sparrow service, model, or
source checkout is required.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

FIXTURE_SCHEMA = json.dumps({
    'invoice_no': 'int',
    'seller_name': 'str',
    'total': 'float or null',
    'items': [{'description': 'str', 'quantity': 'float'}],
})
FIXTURE_VALID = json.dumps({
    'invoice_no': 61356291,
    'seller_name': 'Chapman, Kim and Green',
    'total': None,
    'items': [{'description': 'Wine Glasses', 'quantity': 5.0}],
})
FIXTURE_INVALID = json.dumps({
    'invoice_no': '61356291',
    'seller_name': None,
    'total': 'unknown',
    'items': [{'description': 'Wine Glasses', 'quantity': 'five'}],
})

NUMERIC_TEXT_RE = re.compile(r'^[0-9]+(\.[0-9]+)?$')


@dataclass
class CaseResult:
    name: str
    errors: List[str]
    expected: str

    @property
    def passed_validation(self) -> bool:
        return not self.errors

    @property
    def met_expectation(self) -> bool:
        if self.expected == 'any':
            return True
        if self.expected == 'pass':
            return self.passed_validation
        if self.expected == 'fail':
            return not self.passed_validation
        return False


def load_text(value: Optional[str], file_path: Optional[Path], label: str) -> Optional[str]:
    if value is not None:
        return value
    if file_path is not None:
        return file_path.read_text(encoding='utf-8')
    return None


def load_json(text: str, label: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'{label} is not valid JSON: {exc}') from exc


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: Any) -> bool:
    return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)


def is_numeric_text(value: Any) -> bool:
    return isinstance(value, str) and bool(NUMERIC_TEXT_RE.match(value.strip()))


def validate_type_token(token: str, candidate: Any, path: str) -> List[str]:
    token_norm = token.lower().strip()
    if token_norm == 'str':
        return [] if isinstance(candidate, str) else [f'{path}: expected string, got {type(candidate).__name__}']
    if token_norm == 'int':
        return [] if is_int(candidate) else [f'{path}: expected integer, got {type(candidate).__name__}']
    if token_norm == 'float':
        return [] if is_number(candidate) else [f'{path}: expected number, got {type(candidate).__name__}']

    if token_norm.endswith(' or null'):
        base = token_norm.replace(' or null', '').strip()
        if candidate is None:
            return []
        if base == 'str':
            return validate_type_token('str', candidate, path)
        if base == 'int':
            return validate_type_token('int', candidate, path)
        if base == 'float':
            return validate_type_token('float', candidate, path)
        # Numeric example strings such as "0 or null" and "0.0 or null" accept
        # numbers or numeric strings, matching the documented schema behavior.
        try:
            float(base)
        except ValueError:
            raise ValueError(f'{path}: unsupported type token {token!r}')
        if is_number(candidate) or is_numeric_text(candidate):
            return []
        return [f'{path}: expected number/numeric string/null, got {candidate!r}']

    raise ValueError(f'{path}: unsupported type token {token!r}')


def validate_value(example: Any, candidate: Any, path: str) -> List[str]:
    errors: List[str] = []

    if isinstance(example, dict):
        if not isinstance(candidate, dict):
            return [f'{path}: expected object, got {type(candidate).__name__}']
        for key, child_example in example.items():
            child_path = f'{path}.{key}' if path else key
            if key not in candidate:
                errors.append(f'{child_path}: missing required field')
                continue
            errors.extend(validate_value(child_example, candidate[key], child_path))
        return errors

    if isinstance(example, list):
        if not example:
            raise ValueError(f'{path}: empty arrays are not valid schema examples')
        if not isinstance(candidate, list):
            return [f'{path}: expected array, got {type(candidate).__name__}']
        for idx, item in enumerate(candidate):
            errors.extend(validate_value(example[0], item, f'{path}[{idx}]'))
        return errors

    if is_int(example):
        return [] if is_int(candidate) else [f'{path}: expected integer, got {type(candidate).__name__}']
    if isinstance(example, float):
        return [] if is_number(candidate) else [f'{path}: expected number, got {type(candidate).__name__}']
    if isinstance(example, str):
        return validate_type_token(example, candidate, path)

    raise ValueError(f'{path}: unsupported schema example value type {type(example).__name__}')


def normalize_candidate_shape(example: Any, candidate: Any) -> Any:
    """Match Sparrow's object/array one-level normalization behavior."""
    schema_expects_array = isinstance(example, list)
    candidate_is_array = isinstance(candidate, list)
    if schema_expects_array and not candidate_is_array:
        return [candidate]
    if not schema_expects_array and candidate_is_array:
        return candidate[0] if candidate else {}
    return candidate


def run_case(name: str, schema_text: str, candidate_text: str, expected: str) -> CaseResult:
    errors: List[str] = []
    try:
        schema_example = load_json(schema_text, f'{name} schema')
        candidate = load_json(candidate_text, f'{name} candidate')
        candidate = normalize_candidate_shape(schema_example, candidate)
        errors.extend(validate_value(schema_example, candidate, '$'))
    except ValueError as exc:
        errors.append(str(exc))
    return CaseResult(name=name, errors=errors, expected=expected)


def print_result(result: CaseResult, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps({
            'case': result.name,
            'validation_passed': result.passed_validation,
            'expected': result.expected,
            'expectation_met': result.met_expectation,
            'errors': result.errors,
        }, indent=2))
        return

    status = 'PASS' if result.passed_validation else 'FAIL'
    expectation = 'ok' if result.met_expectation else 'unexpected'
    print(f'{result.name}: validation={status}; expectation={result.expected} ({expectation})')
    for error in result.errors:
        print(f'  - {error}')


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Validate a Sparrow-style JSON example schema against candidate JSON using offline fixtures by default.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--schema', help='Sparrow JSON example schema string.')
    parser.add_argument('--schema-file', type=Path, help='File containing the Sparrow JSON example schema.')
    parser.add_argument('--candidate', help='Candidate model-response JSON string.')
    parser.add_argument('--candidate-file', type=Path, help='File containing candidate model-response JSON.')
    parser.add_argument('--expect', choices=['pass', 'fail', 'any'], default='pass', help='Expected outcome for a custom schema/candidate case.')
    parser.add_argument('--fixture', choices=['both', 'valid', 'invalid'], default='both', help='Fixture case to run when no custom schema/candidate is provided.')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable result objects.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    schema_text = load_text(args.schema, args.schema_file, 'schema')
    candidate_text = load_text(args.candidate, args.candidate_file, 'candidate')
    custom_mode = schema_text is not None or candidate_text is not None

    results: List[CaseResult]
    if custom_mode:
        if schema_text is None or candidate_text is None:
            parser.error('custom mode requires both schema and candidate input')
        results = [run_case('custom', schema_text, candidate_text, args.expect)]
    else:
        results = []
        if args.fixture in {'both', 'valid'}:
            results.append(run_case('fixture-valid', FIXTURE_SCHEMA, FIXTURE_VALID, 'pass'))
        if args.fixture in {'both', 'invalid'}:
            results.append(run_case('fixture-invalid', FIXTURE_SCHEMA, FIXTURE_INVALID, 'fail'))

    for idx, result in enumerate(results):
        if idx:
            print()
        print_result(result, as_json=args.json)

    return 0 if all(result.met_expectation for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
