#!/usr/bin/env python3
"""Build a safe MUNIT training command without launching training.

The helper validates obvious static inputs and prints the command that should be
run from a user-provided MUNIT checkout. It never imports MUNIT, allocates CUDA,
downloads data, or starts the training loop.
"""
import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_yaml(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        import yaml  # type: ignore
        with path.open('r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle)
        return data if isinstance(data, dict) else {}, 'pyyaml.safe_load'
    except Exception:
        data: Dict[str, Any] = {}
        stack: List[Tuple[int, Dict[str, Any]]] = [(0, data)]
        for raw in path.read_text(encoding='utf-8').splitlines():
            line = raw.split('#', 1)[0].rstrip()
            if not line.strip() or ':' not in line:
                continue
            indent = len(line) - len(line.lstrip(' '))
            key, value = line.strip().split(':', 1)
            key = key.strip()
            value = value.strip()
            while stack and indent < stack[-1][0]:
                stack.pop()
            current = stack[-1][1]
            if value == '':
                current[key] = {}
                stack.append((indent + 2, current[key]))
            else:
                lower = value.lower()
                if lower in {'true', 'false'}:
                    current[key] = lower == 'true'
                else:
                    try:
                        current[key] = int(value)
                    except ValueError:
                        try:
                            current[key] = float(value)
                        except ValueError:
                            current[key] = value.strip('"\'')
        return data, 'built-in-simple-yaml'


def resolve(path_text: str, repo_root: Path) -> Path:
    p = Path(path_text)
    return p if p.is_absolute() else repo_root / p


def quote_cmd(parts: List[str]) -> str:
    return ' '.join(shlex.quote(p) for p in parts)


def checkpoint_dir(output_path: Path, config: Path) -> Path:
    model_name = config.stem
    return output_path / 'outputs' / model_name / 'checkpoints'


def main() -> int:
    parser = argparse.ArgumentParser(description='Print and validate a MUNIT training command; does not execute training.')
    parser.add_argument('--config', required=True, help='MUNIT YAML config path, relative to --repo-root unless absolute.')
    parser.add_argument('--output-path', default='.', help='Training output root passed to train.py as --output_path.')
    parser.add_argument('--trainer', choices=['MUNIT', 'UNIT'], default='MUNIT', help='Trainer implementation.')
    parser.add_argument('--resume', action='store_true', help='Include --resume and check checkpoint directory shape.')
    parser.add_argument('--repo-root', default='.', help="User's MUNIT checkout root containing train.py.")
    parser.add_argument('--python', default='python', help='Python executable name/path to place in the printed command.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report instead of text.')
    parser.add_argument('--allow-missing-data', action='store_true', help='Do not fail when config-referenced dataset paths are missing.')
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    config_path = resolve(args.config, repo_root)
    output_path = resolve(args.output_path, repo_root)
    errors: List[str] = []
    warnings: List[str] = []

    train_py = repo_root / 'train.py'
    if not train_py.is_file():
        errors.append(f'train.py not found under repo root: {train_py}')
    if not config_path.is_file():
        errors.append(f'config file not found: {config_path}')
        conf: Dict[str, Any] = {}
        parser_name = 'not-parsed'
    else:
        conf, parser_name = load_yaml(config_path)

    if conf:
        if args.trainer == 'UNIT':
            missing = [k for k in ['recon_kl_w', 'recon_kl_cyc_w'] if k not in conf]
            if missing:
                errors.append(f'UNIT trainer selected but config lacks UNIT KL keys: {missing}')
        else:
            missing = [k for k in ['recon_s_w', 'recon_c_w'] if k not in conf]
            if missing:
                errors.append(f'MUNIT trainer selected but config lacks MUNIT keys: {missing}')
        if conf.get('vgg_w', 0):
            warnings.append('vgg_w is positive; original utility may create/download/convert VGG files under output_path/models')
        display_size = conf.get('display_size')
        if not isinstance(display_size, int) or display_size <= 0:
            errors.append(f'display_size should be a positive integer, observed {display_size!r}')
        if 'data_root' in conf:
            data_root = resolve(str(conf['data_root']), repo_root)
            for split in ['trainA', 'trainB', 'testA', 'testB']:
                if not (data_root / split).is_dir():
                    msg = f'data_root split missing: {data_root / split}'
                    (warnings if args.allow_missing_data else errors).append(msg)
        else:
            keys = ['data_folder_train_a', 'data_list_train_a', 'data_folder_test_a', 'data_list_test_a', 'data_folder_train_b', 'data_list_train_b', 'data_folder_test_b', 'data_list_test_b']
            for key in keys:
                if key not in conf:
                    errors.append(f'list-mode config missing {key}')
                else:
                    p = resolve(str(conf[key]), repo_root)
                    if not p.exists():
                        msg = f'list-mode path for {key} does not exist: {p}'
                        (warnings if args.allow_missing_data else errors).append(msg)

    cmd = [args.python, 'train.py', '--config', args.config, '--output_path', args.output_path, '--trainer', args.trainer]
    if args.resume:
        cmd.append('--resume')
        ckpt = checkpoint_dir(output_path, config_path)
        gen = sorted(ckpt.glob('*gen*.pt')) if ckpt.is_dir() else []
        dis = sorted(ckpt.glob('*dis*.pt')) if ckpt.is_dir() else []
        opt = ckpt / 'optimizer.pt'
        if not ckpt.is_dir():
            errors.append(f'resume requested but checkpoint directory is missing: {ckpt}')
        else:
            if not gen:
                errors.append(f'resume requested but no generator checkpoint found in {ckpt}')
            if not dis:
                errors.append(f'resume requested but no discriminator checkpoint found in {ckpt}')
            if not opt.is_file():
                errors.append(f'resume requested but optimizer.pt is missing in {ckpt}')

    report = {
        'repo_root': str(repo_root),
        'config': str(config_path),
        'output_path': str(output_path),
        'trainer': args.trainer,
        'resume': args.resume,
        'parser': parser_name,
        'command': cmd,
        'shell_command': quote_cmd(cmd),
        'run_from': str(repo_root),
        'warnings': warnings,
        'errors': errors,
        'notes': [
            'This helper does not execute training.',
            'The original MUNIT training path calls CUDA unconditionally; use a compatible legacy CUDA runtime before running the command.',
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('MUNIT training command dry run')
        print(f'run from: {repo_root}')
        print('command:')
        print('  ' + report['shell_command'])
        for item in warnings:
            print('WARN ' + item)
        for item in errors:
            print('FAIL ' + item)
        if not errors:
            print('OK command is statically ready; execute only after CUDA/runtime and user approval gates pass')
    return 2 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
