#!/usr/bin/env python3
"""Build safe Sparrow CLI or curl request templates.

The script never sends a request and never reads document inputs. It only formats
commands from structured arguments or from a captured curl command.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_QUERY = '[{"field_name":"str", "amount":0}]'
DEFAULT_INSTRUCTION_QUERY = 'instruction: do arithmetic, payload: 2+2='
DEFAULT_PIPELINE = 'sparrow-parse'
DEFAULT_INSTRUCTION_PIPELINE = 'sparrow-instructor'
DEFAULT_OPTIONS = ['mlx', 'mlx-community/Qwen2.5-VL-72B-Instruct-4bit']
BOOL_FIELDS = ['instruction', 'validation', 'ocr', 'markdown', 'table', 'debug']


@dataclass
class RequestSpec:
    query: Optional[str] = None
    pipeline: Optional[str] = None
    options: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    hints_file_path: Optional[str] = None
    crop_size: Optional[str] = None
    page_types: List[str] = field(default_factory=list)
    table_template: Optional[str] = None
    debug_dir: Optional[str] = None
    instruction: bool = False
    validation: bool = False
    ocr: bool = False
    markdown: bool = False
    table: bool = False
    debug: bool = False
    sparrow_key: Optional[str] = None
    client_ip: Optional[str] = None
    country: Optional[str] = None
    endpoint: Optional[str] = None


def split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(',') if part.strip()]


def clean_upload_value(value: str) -> str:
    """Convert curl form upload syntax like @document.pdf;type=... to a path."""
    value = value.strip()
    if value.startswith('@'):
        value = value[1:]
    if ';' in value:
        value = value.split(';', 1)[0]
    return value


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def parse_curl_forms(text: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Extract simple -F/-d key=value fields and the request URL from a curl command."""
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError as exc:
        raise SystemExit(f'Could not parse curl text with shell quoting: {exc}') from exc

    forms: Dict[str, str] = {}
    url: Optional[str] = None
    value_flags = {
        '-F', '--form', '--form-string',
        '-d', '--data', '--data-raw', '--data-binary', '--data-urlencode',
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith('http://') or token.startswith('https://'):
            url = token
        if token in value_flags and i + 1 < len(tokens):
            item = tokens[i + 1]
            if '=' in item:
                key, value = item.split('=', 1)
                forms[key] = value
            i += 2
            continue
        i += 1

    return forms, url


def spec_from_forms(forms: Dict[str, str], url: Optional[str]) -> RequestSpec:
    spec = RequestSpec()
    if url and 'instruction-inference' in url:
        spec.endpoint = 'instruction-inference'
    elif url and 'inference' in url:
        spec.endpoint = 'inference'

    spec.query = forms.get('query')
    spec.pipeline = forms.get('pipeline')
    spec.options = split_csv(forms.get('options'))
    spec.crop_size = forms.get('crop_size')
    spec.page_types = split_csv(forms.get('page_type'))
    spec.table_template = forms.get('table_template')
    spec.debug_dir = forms.get('debug_dir')
    spec.sparrow_key = forms.get('sparrow_key')
    spec.client_ip = forms.get('client_ip')
    spec.country = forms.get('country')

    if 'file' in forms:
        spec.file_path = clean_upload_value(forms['file'])
    if 'hints_file' in forms:
        spec.hints_file_path = clean_upload_value(forms['hints_file'])

    for field_name in BOOL_FIELDS:
        if field_name in forms:
            setattr(spec, field_name, parse_bool(forms[field_name]))

    return spec


def merge_specs(base: RequestSpec, override: RequestSpec) -> RequestSpec:
    """Merge non-empty values from override onto base."""
    result = RequestSpec(**base.__dict__)
    for key, value in override.__dict__.items():
        if isinstance(value, list):
            if value:
                setattr(result, key, value)
        elif isinstance(value, bool):
            if value:
                setattr(result, key, value)
        elif value is not None:
            setattr(result, key, value)
    return result


def shell_join_multiline(parts: List[str]) -> str:
    quoted = [shlex.quote(str(part)) for part in parts]
    if len(quoted) <= 6:
        return ' '.join(quoted)
    if quoted[0] == 'curl':
        lines = [quoted[0] + ' \\']
        rest = quoted[1:]
    else:
        lines = [' '.join(quoted[:2]) + ' \\']
        rest = quoted[2:]
    pairs = []
    i = 0
    while i < len(rest):
        if rest[i].startswith('-') and i + 1 < len(rest) and not rest[i + 1].startswith('-'):
            pairs.append(rest[i] + ' ' + rest[i + 1])
            i += 2
        else:
            pairs.append(rest[i])
            i += 1
    for idx, pair in enumerate(pairs):
        suffix = ' \\' if idx < len(pairs) - 1 else ''
        lines.append('  ' + pair + suffix)
    return '\n'.join(lines)


def finalize_spec(spec: RequestSpec, endpoint_hint: Optional[str]) -> RequestSpec:
    endpoint = spec.endpoint or endpoint_hint or 'inference'
    instruction_endpoint = endpoint == 'instruction-inference'
    spec.endpoint = endpoint

    if not spec.query:
        spec.query = DEFAULT_INSTRUCTION_QUERY if instruction_endpoint else DEFAULT_QUERY
    if not spec.pipeline:
        spec.pipeline = DEFAULT_INSTRUCTION_PIPELINE if instruction_endpoint else DEFAULT_PIPELINE
    if not spec.options:
        spec.options = list(DEFAULT_OPTIONS)
    if not instruction_endpoint and not spec.file_path:
        spec.file_path = 'document.pdf'
    return spec


def build_cli(spec: RequestSpec) -> str:
    parts = ['./sparrow.sh']
    if spec.endpoint == 'instruction-inference' and spec.pipeline == DEFAULT_INSTRUCTION_PIPELINE:
        # The normal LLM instruction path is still engine.py via sparrow.sh; the
        # special "assistant" first token is intentionally not emitted here.
        pass
    parts.append(spec.query or DEFAULT_QUERY)
    parts += ['--pipeline', spec.pipeline or DEFAULT_PIPELINE]

    for option in spec.options:
        parts += ['--options', option]
    if spec.file_path:
        parts += ['--file-path', spec.file_path]
    if spec.hints_file_path:
        parts += ['--hints-file-path', spec.hints_file_path]
    if spec.crop_size:
        parts += ['--crop-size', spec.crop_size]
    for page_type in spec.page_types:
        parts += ['--page-type', page_type]
    if spec.table_template:
        parts += ['--table-template', spec.table_template]
    if spec.debug_dir:
        parts += ['--debug-dir', spec.debug_dir]
    for flag in BOOL_FIELDS:
        if getattr(spec, flag):
            parts.append(f'--{flag.replace("_", "-")}')

    return shell_join_multiline(parts)


def add_curl_field(parts: List[str], key: str, value: object, form_flag: str = '-F') -> None:
    if value is None or value == '' or value is False:
        return
    if value is True:
        value = 'true'
    parts += [form_flag, f'{key}={value}']


def build_curl(spec: RequestSpec, base_url: str) -> str:
    endpoint = spec.endpoint or 'inference'
    url = base_url.rstrip('/') + f'/api/v1/sparrow-llm/{endpoint}'
    parts = ['curl', '-X', 'POST', url]

    if endpoint == 'instruction-inference':
        parts += ['-H', 'Content-Type: application/x-www-form-urlencoded']
        form_flag = '-d'
        add_curl_field(parts, 'query', spec.query, form_flag)
        add_curl_field(parts, 'pipeline', spec.pipeline, form_flag)
        add_curl_field(parts, 'options', ','.join(spec.options), form_flag)
        add_curl_field(parts, 'debug_dir', spec.debug_dir, form_flag)
        add_curl_field(parts, 'debug', spec.debug, form_flag)
        add_curl_field(parts, 'sparrow_key', spec.sparrow_key, form_flag)
        add_curl_field(parts, 'client_ip', spec.client_ip, form_flag)
        add_curl_field(parts, 'country', spec.country, form_flag)
    else:
        parts += ['-H', 'Content-Type: multipart/form-data']
        add_curl_field(parts, 'query', spec.query)
        add_curl_field(parts, 'pipeline', spec.pipeline)
        add_curl_field(parts, 'options', ','.join(spec.options))
        add_curl_field(parts, 'crop_size', spec.crop_size)
        add_curl_field(parts, 'instruction', spec.instruction)
        add_curl_field(parts, 'validation', spec.validation)
        add_curl_field(parts, 'ocr', spec.ocr)
        add_curl_field(parts, 'markdown', spec.markdown)
        add_curl_field(parts, 'table', spec.table)
        add_curl_field(parts, 'table_template', spec.table_template)
        if spec.page_types:
            add_curl_field(parts, 'page_type', ','.join(spec.page_types))
        add_curl_field(parts, 'debug_dir', spec.debug_dir)
        add_curl_field(parts, 'debug', spec.debug)
        add_curl_field(parts, 'sparrow_key', spec.sparrow_key)
        add_curl_field(parts, 'client_ip', spec.client_ip)
        add_curl_field(parts, 'country', spec.country)
        if spec.file_path:
            add_curl_field(parts, 'file', '@' + spec.file_path)
        if spec.hints_file_path:
            add_curl_field(parts, 'hints_file', '@' + spec.hints_file_path)

    return shell_join_multiline(parts)


def spec_to_json(spec: RequestSpec) -> str:
    return json.dumps(spec.__dict__, indent=2, ensure_ascii=False)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Build offline Sparrow CLI/curl request templates; no network call is made.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--surface', choices=['cli', 'curl', 'json'], default='cli', help='Output format to emit.')
    parser.add_argument('--from-curl', help='Curl command text to parse and normalize.')
    parser.add_argument('--from-curl-file', type=Path, help='File containing a curl command to parse and normalize.')
    parser.add_argument('--base-url', default='http://localhost:8002', help='Base URL used when emitting curl.')
    parser.add_argument('--endpoint', choices=['inference', 'instruction-inference'], help='API endpoint mode.')

    parser.add_argument('--query', help='Sparrow query. Uses a safe fixture when omitted.')
    parser.add_argument('--pipeline', help='Pipeline name.')
    parser.add_argument('--option', dest='options', action='append', help='Repeat to add CLI/API option entries.')
    parser.add_argument('--options-csv', help='Comma-separated option entries, matching API form syntax.')
    parser.add_argument('--backend', help='Backend method used when --option/--options-csv are omitted.')
    parser.add_argument('--model', help='Model or hosted space used when --option/--options-csv are omitted.')
    parser.add_argument('--file-path', help='Document path placeholder for emitted requests.')
    parser.add_argument('--hints-file-path', help='Hints JSON path placeholder for emitted requests.')
    parser.add_argument('--crop-size', help='Crop size string to include in the request.')
    parser.add_argument('--page-type', dest='page_types', action='append', help='Repeat for CLI page types; emitted as comma-separated API field.')
    parser.add_argument('--table-template', help='Table template basename, e.g. sparrow_generic_table.')
    parser.add_argument('--debug-dir', help='Debug output directory placeholder.')
    parser.add_argument('--sparrow-key', help='Protected-access key placeholder.')
    parser.add_argument('--client-ip', help='Client IP metadata for API logging.')
    parser.add_argument('--country', help='Country metadata for API logging.')

    for field_name in BOOL_FIELDS:
        parser.add_argument(f'--{field_name.replace("_", "-")}', action='store_true', help=f'Include {field_name}=true / --{field_name.replace("_", "-")} flag.')

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    parsed = RequestSpec()
    curl_text_parts = []
    if args.from_curl:
        curl_text_parts.append(args.from_curl)
    if args.from_curl_file:
        curl_text_parts.append(args.from_curl_file.read_text(encoding='utf-8'))
    if curl_text_parts:
        forms, url = parse_curl_forms('\n'.join(curl_text_parts))
        parsed = spec_from_forms(forms, url)

    explicit_options: List[str] = []
    if args.options_csv:
        explicit_options.extend(split_csv(args.options_csv))
    if args.options:
        explicit_options.extend(args.options)
    if not explicit_options and (args.backend or args.model):
        explicit_options = [args.backend or DEFAULT_OPTIONS[0], args.model or DEFAULT_OPTIONS[1]]

    explicit = RequestSpec(
        query=args.query,
        pipeline=args.pipeline,
        options=explicit_options,
        file_path=args.file_path,
        hints_file_path=args.hints_file_path,
        crop_size=args.crop_size,
        page_types=args.page_types or [],
        table_template=args.table_template,
        debug_dir=args.debug_dir,
        sparrow_key=args.sparrow_key,
        client_ip=args.client_ip,
        country=args.country,
        endpoint=args.endpoint,
    )
    for field_name in BOOL_FIELDS:
        setattr(explicit, field_name, getattr(args, field_name))

    spec = finalize_spec(merge_specs(parsed, explicit), args.endpoint)

    print('# Offline Sparrow request template; this script did not contact a server or read document files.')
    if spec.file_path == 'document.pdf':
        print('# Replace document.pdf with a real file path before manual execution.')

    if args.surface == 'cli':
        print(build_cli(spec))
    elif args.surface == 'curl':
        print(build_curl(spec, args.base_url))
    else:
        print(spec_to_json(spec))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
