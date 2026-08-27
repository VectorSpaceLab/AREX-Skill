#!/usr/bin/env python3
"""Print safe NeMo maintainer validation commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Command:
    category: str
    command: tuple[str, ...]
    reason: str


def normalize_path(path: str) -> str:
    normalized = path.strip().replace('\\', '/')
    while normalized.startswith('./'):
        normalized = normalized[2:]
    return normalized.strip('/')


def quote_command(parts: Iterable[str]) -> str:
    return ' '.join(shlex.quote(part) for part in parts)


def add_command(commands: list[Command], category: str, command: Iterable[str], reason: str) -> None:
    candidate = Command(category=category, command=tuple(command), reason=reason)
    if candidate not in commands:
        commands.append(candidate)


def has_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix.rstrip('/') + '/')


def path_parent(path: str) -> str:
    parent = str(PurePosixPath(path).parent)
    return '' if parent == '.' else parent


def collect_python_targets(paths: list[str]) -> list[str]:
    targets: list[str] = []
    for path in paths:
        if not path:
            continue
        if path.endswith('.py') or has_prefix(path, 'nemo') or has_prefix(path, 'tests') or has_prefix(path, 'scripts'):
            target = path if path.endswith('.py') else path.split('/')[0] if '/' not in path else path
            if target not in targets:
                targets.append(target)
    return targets


def infer_commands(paths: list[str], keywords: list[str], include_docs: bool) -> list[Command]:
    commands: list[Command] = []
    lowered_keywords = {keyword.lower().strip() for keyword in keywords if keyword.strip()}

    def touched(prefix: str) -> bool:
        return any(has_prefix(path, prefix) for path in paths)

    def keyword(*names: str) -> bool:
        return bool(lowered_keywords.intersection(names))

    if touched('nemo/collections/asr') or touched('tests/collections/asr') or keyword('asr', 'transcription', 'rnnt', 'ctc', 'tdt', 'canary'):
        add_command(commands, 'pytest', ['pytest', 'tests/collections/asr', '-m', 'not pleasefixme', '-v'], 'ASR collection or ASR keyword changed.')

    if touched('nemo/collections/audio') or touched('tests/collections/audio') or keyword('audio', 'enhancement', 'separation', 'denoise'):
        add_command(commands, 'pytest', ['pytest', 'tests/collections/audio', '-m', 'not pleasefixme', '-v'], 'Audio collection or audio keyword changed.')

    if touched('nemo/collections/tts') or touched('tests/collections/tts') or keyword('tts', 'magpie', 'fastpitch', 'hifigan', 'g2p'):
        add_command(commands, 'pytest', ['pytest', 'tests/collections/tts', '-m', 'unit and not pleasefixme', '-v'], 'TTS collection changed; unit subset is the fast default.')

    if touched('nemo/collections/speechlm2') or touched('tests/collections/speechlm2') or keyword('speechlm2', 'salm', 'automodel', 'voicechat', 'vllm'):
        add_command(commands, 'pytest', ['pytest', 'tests/collections/speechlm2', '-m', 'not pleasefixme', '-v'], 'SpeechLM2 collection or related keyword changed.')

    if touched('nemo/collections/common') or touched('tests/collections/common') or keyword('common', 'lhotse', 'tokenizer', 'prompt'):
        add_command(commands, 'pytest', ['pytest', 'tests/collections/common', '-m', 'not pleasefixme', '-v'], 'Common collection, Lhotse, tokenizer, or prompt code changed.')

    if touched('nemo/collections/speaker_tasks') or touched('tests/collections/speaker_tasks') or keyword('speaker', 'diarization', 'vad', 'alignment', 'rttm'):
        add_command(commands, 'pytest', ['pytest', 'tests/collections/speaker_tasks', '-m', 'not pleasefixme', '-v'], 'Speaker, diarization, or VAD code changed.')

    if touched('nemo/core') or touched('tests/core') or keyword('core', 'modelpt', 'save_restore', 'safe_instantiate'):
        add_command(commands, 'pytest', ['pytest', 'tests/core', '-m', 'not pleasefixme', '-v'], 'Core framework code changed.')

    if touched('tests/core_ptl') or keyword('pytorch-lightning', 'lightning-trainer'):
        add_command(commands, 'pytest', ['pytest', 'tests/core_ptl', '-m', 'not pleasefixme', '-v'], 'PyTorch Lightning core integration changed.')

    if touched('nemo/utils') or touched('tests/utils') or keyword('utils', 'exp_manager', 'checkpoint', 'trainer'):
        add_command(commands, 'pytest', ['pytest', 'tests/utils', '-m', 'not pleasefixme', '-v'], 'Shared utility code changed.')

    if touched('nemo/lightning') or touched('tests/lightning') or keyword('lightning', 'fsdp', 'strategy'):
        add_command(commands, 'pytest', ['pytest', 'tests/lightning', '-m', 'not pleasefixme', '-v'], 'Lightning integration code changed.')

    if touched('tests/hydra') or touched('nemo/core/config') or keyword('hydra', 'omegaconf', 'config'):
        add_command(commands, 'pytest', ['pytest', 'tests/hydra', '-m', 'not pleasefixme', '-v'], 'Hydra or OmegaConf configuration code changed.')

    exact_tests = [path for path in paths if path.startswith('tests/') and path.endswith('.py')]
    for test_path in exact_tests[:5]:
        add_command(commands, 'pytest', ['pytest', test_path, '-m', 'not pleasefixme', '-v'], 'Touched test file; run it before broader suites.')

    docs_touched = touched('docs') or any(path.endswith(('.rst', '.md')) for path in paths) or keyword('docs', 'documentation', 'sphinx')
    if include_docs or docs_touched:
        add_command(commands, 'docs', ['uv', 'run', 'make', '-C', 'docs', 'html'], 'Docs or Markdown/reStructuredText changed.')
        add_command(commands, 'docs', ['uv', 'run', 'make', '-C', 'docs', 'clean', 'html'], 'Use after toctree, config, or structural docs changes.')

    python_targets = collect_python_targets(paths)
    if python_targets:
        add_command(commands, 'format', ['isort', '--check', *python_targets], 'Check import ordering for touched Python targets.')
        add_command(commands, 'format', ['black', '--check', *python_targets], 'Check Black formatting for touched Python targets.')
    elif keyword('format', 'style', 'lint'):
        add_command(commands, 'format', ['isort', '--check', '.'], 'No changed Python paths supplied; broad style check requested.')
        add_command(commands, 'format', ['black', '--check', '.'], 'No changed Python paths supplied; broad style check requested.')

    if touched('.github/workflows'):
        add_command(commands, 'warning', ['printf', '%s\n', 'CI workflow files changed: do not modify or validate broadly unless explicitly requested.'], 'Workflow files are normally evidence-only for this skill.')

    if not commands:
        add_command(commands, 'inspect', ['pytest', '--markers'], 'No specific mapping matched; inspect markers and choose a focused test manually.')

    return commands


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Print focused NeMo repository validation commands from changed paths or capability keywords. Commands are not executed.',
    )
    parser.add_argument('--changed', nargs='*', default=[], help='Changed repo-relative paths, such as nemo/core/foo.py tests/core/test_foo.py.')
    parser.add_argument('--changed-file', help='File containing one changed repo-relative path per line, for example from git diff --name-only.')
    parser.add_argument('--keyword', action='append', default=[], help='Capability keyword such as asr, docs, hydra, speechlm2, cuda, tts, audio, or diarization. May repeat.')
    parser.add_argument('--docs', action='store_true', help='Include docs build suggestions even if no docs paths are supplied.')
    parser.add_argument('--json', action='store_true', help='Emit a JSON array instead of human-readable text.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = [normalize_path(path) for path in args.changed]
    if args.changed_file:
        with open(args.changed_file, 'r', encoding='utf-8') as handle:
            paths.extend(normalize_path(line) for line in handle if line.strip())
    paths = [path for path in paths if path]

    commands = infer_commands(paths, args.keyword, args.docs)

    if args.json:
        import json

        print(
            json.dumps(
                [
                    {'category': command.category, 'command': list(command.command), 'reason': command.reason}
                    for command in commands
                ],
                indent=2,
            )
        )
    else:
        print('Safe command plan only; nothing was executed. Review hardware/network/runtime cost before running.')
        for index, command in enumerate(commands, start=1):
            print(f'\n{index}. [{command.category}] {command.reason}')
            print(f'   {quote_command(command.command)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
