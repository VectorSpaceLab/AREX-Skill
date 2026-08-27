#!/usr/bin/env python3
"""Render tiny OpenCompass-style prompt previews without datasets or models.

This helper mirrors the core behavior agents usually need to debug:
- missing fields remain literal;
- the generation output column is masked;
- ICE examples are inserted through an ice token;
- PPL candidate templates are selected by label;
- dialogue templates render as a PromptList-like list of role dictionaries.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from string import Formatter
from typing import Any

ICE_TOKEN = '</E>'
OUTPUT_COLUMN = 'answer'

TRAIN = [
    {
        'question': '2+2=?',
        'answer': '4',
        'A': '3',
        'B': '4',
    },
    {
        'question': '3+3=?',
        'answer': '6',
        'A': '6',
        'B': '7',
    },
]

TEST = {
    'question': '1+1=?',
    'answer': '2',
    'A': '1',
    'B': '2',
}

GEN_ICE_TEMPLATE = 'Q: {question}\nA: {answer}'
GEN_PROMPT_TEMPLATE = 'Solve the following questions.\n</E>Q: {question}\nA: {answer}'

PPL_PROMPT_TEMPLATE = {
    'A': 'Q: {question}\nA. {A}\nB. {B}\nAnswer: A',
    'B': 'Q: {question}\nA. {A}\nB. {B}\nAnswer: B',
}

DIALOGUE_TEMPLATE = {
    'begin': [
        {
            'role': 'SYSTEM',
            'fallback_role': 'HUMAN',
            'prompt': 'Solve the following questions.',
        },
        ICE_TOKEN,
    ],
    'round': [
        {
            'role': 'HUMAN',
            'prompt': 'Question: {question}',
        },
        {
            'role': 'BOT',
            'prompt': 'Answer: {answer}',
        },
    ],
}

MISSING_FIELD_TEMPLATE = 'Q: {question}\nContext: {context}\nA: {answer}'


class PreserveMissing(dict):
    def __missing__(self, key: str) -> str:
        return '{' + key + '}'


def safe_format(template: str, entry: dict[str, Any]) -> str:
    field_names = [name for _, name, _, _ in Formatter().parse(template) if name]
    values = PreserveMissing({name: entry[name] for name in field_names if name in entry})
    return template.format_map(values)


def mask_entry(entry: dict[str, Any], output_column: str, replacement: str) -> dict[str, Any]:
    masked = deepcopy(entry)
    if output_column:
        masked[output_column] = replacement
    return masked


def render_string_gen(gen_field_replace_token: str, include_ice: bool) -> str:
    ice = ''
    if include_ice:
        ice = '\n'.join(safe_format(GEN_ICE_TEMPLATE, row) for row in TRAIN) + '\n'
    test_entry = mask_entry(TEST, OUTPUT_COLUMN, gen_field_replace_token)
    return safe_format(GEN_PROMPT_TEMPLATE.replace(ICE_TOKEN, ice), test_entry)


def render_ppl(label: str) -> str:
    if label not in PPL_PROMPT_TEMPLATE:
        choices = ', '.join(sorted(PPL_PROMPT_TEMPLATE))
        raise SystemExit(f'Unknown label {label!r}; choose one of: {choices}')
    return safe_format(PPL_PROMPT_TEMPLATE[label], TEST)


def format_dialogue_items(items: list[Any], entry: dict[str, Any]) -> list[Any]:
    rendered = []
    for item in items:
        if isinstance(item, str):
            rendered.append(item)
            continue
        new_item = deepcopy(item)
        if 'prompt' in new_item:
            new_item['prompt'] = safe_format(new_item['prompt'], entry)
        rendered.append(new_item)
    return rendered


def render_dialogue(gen_field_replace_token: str, include_ice: bool) -> list[Any]:
    prompt_list: list[Any] = []
    prompt_list.append({'section': 'begin', 'pos': 'begin'})
    for item in DIALOGUE_TEMPLATE['begin']:
        if item == ICE_TOKEN and include_ice:
            prompt_list.append({'section': 'ice', 'pos': 'begin'})
            for row in TRAIN:
                prompt_list.extend(format_dialogue_items(DIALOGUE_TEMPLATE['round'], row))
            prompt_list.append({'section': 'ice', 'pos': 'end'})
        elif item != ICE_TOKEN:
            prompt_list.extend(format_dialogue_items([item], TEST))
    prompt_list.append({'section': 'begin', 'pos': 'end'})
    prompt_list.append({'section': 'round', 'pos': 'begin'})
    prompt_list.extend(
        format_dialogue_items(
            DIALOGUE_TEMPLATE['round'],
            mask_entry(TEST, OUTPUT_COLUMN, gen_field_replace_token),
        )
    )
    prompt_list.append({'section': 'round', 'pos': 'end'})
    return prompt_list


def flatten_dialogue(prompt_list: list[Any], apply_meta: bool) -> str:
    rendered = []
    for item in prompt_list:
        if not isinstance(item, dict) or 'role' not in item:
            continue
        role = item['role']
        prompt = item.get('prompt', '')
        if apply_meta:
            if role == 'SYSTEM':
                role = item.get('fallback_role', 'HUMAN')
            prefix = {'HUMAN': '<|user|> ', 'BOT': '<|assistant|> '}.get(role, f'<|{role.lower()}|> ')
            if role == 'BOT' and prompt.strip() == 'Answer:':
                rendered.append(prefix)
            else:
                rendered.append(prefix + prompt)
        else:
            rendered.append(prompt)
    return '\n'.join(rendered)


def find_placeholders(text: str) -> list[str]:
    return sorted(set(re.findall(r'\{[^{}]+\}', text)))


def print_diagnostics(rendered: Any, output_column: str) -> None:
    text = json.dumps(rendered, ensure_ascii=False) if not isinstance(rendered, str) else rendered
    placeholders = find_placeholders(text)
    print('\nDiagnostics:')
    print(f'- unresolved placeholders: {placeholders or "none"}')
    print(f'- gold output column: {output_column!r}')
    print(f'- gold answer visible: {str(TEST[output_column]) in text}')
    print('- if answer slot is blank in gen mode, that usually means masking is working')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Preview tiny OpenCompass-style prompt rendering.')
    parser.add_argument('--mode', choices=['gen', 'ppl'], default='gen', help='render a generation or PPL candidate prompt')
    parser.add_argument('--label', default='A', help='candidate label for --mode ppl')
    parser.add_argument('--dialogue', action='store_true', help='render dialogue PromptList-like output instead of string prompt')
    parser.add_argument('--no-ice', action='store_true', help='omit in-context examples')
    parser.add_argument('--gen-field-replace-token', default='', help='safe replacement for the output column in gen prompts')
    parser.add_argument('--missing-field-demo', action='store_true', help='render a template with an unresolved {context} field')
    parser.add_argument('--show-raw', action='store_true', help='for dialogue mode, also show flattened text without and with a tiny meta template')
    parser.add_argument('--json', action='store_true', help='emit JSON for structured inspection')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.missing_field_demo:
        rendered: Any = safe_format(
            MISSING_FIELD_TEMPLATE,
            mask_entry(TEST, OUTPUT_COLUMN, args.gen_field_replace_token),
        )
    elif args.dialogue:
        rendered = render_dialogue(args.gen_field_replace_token, not args.no_ice)
    elif args.mode == 'ppl':
        rendered = render_ppl(args.label)
    else:
        rendered = render_string_gen(args.gen_field_replace_token, not args.no_ice)

    if args.json:
        print(json.dumps(rendered, indent=2, ensure_ascii=False))
    elif isinstance(rendered, str):
        print(rendered)
    else:
        print(json.dumps(rendered, indent=2, ensure_ascii=False))

    if args.dialogue and args.show_raw and isinstance(rendered, list):
        print('\nFlattened without meta_template:')
        print(flatten_dialogue(rendered, apply_meta=False))
        print('\nFlattened with tiny fallback meta_template:')
        print(flatten_dialogue(rendered, apply_meta=True))

    print_diagnostics(rendered, OUTPUT_COLUMN)


if __name__ == '__main__':
    main()
