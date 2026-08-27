#!/usr/bin/env python3
"""Validate Triton model repository layout and simple config expectations.

This helper is intentionally conservative: it checks directory structure,
version folders, config presence, and a few readable config hints without
starting Triton.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Finding:
    severity: str
    model: str
    message: str
    path: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    ok: bool
    repository: str
    summary: dict[str, int]
    findings: list[Finding]
    models: list[dict[str, Any]]


NUMERIC_VERSION = re.compile(r"^[1-9][0-9]*$")


def parse_config(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    # Only treat name as the optional top-level model name. Tensor input/output
    # blocks also contain name fields, so inspect only the prefix before common
    # repeated blocks.
    block_positions = [pos for token in ('\ninput', '\noutput', '\ninstance_group', '\ndynamic_batching', '\nsequence_batching') if (pos := text.find(token)) >= 0]
    top_level_prefix = text[: min(block_positions)] if block_positions else text
    if 'name:' in top_level_prefix:
        m = re.search(r'(?m)^\s*name:\s*"([^"]+)"', top_level_prefix)
        if m: out['name'] = m.group(1)
    if 'backend:' in text:
        m = re.search(r'backend:\s*"([^"]+)"', text)
        if m: out['backend'] = m.group(1)
    if 'platform:' in text:
        m = re.search(r'platform:\s*"([^"]+)"', text)
        if m: out['platform'] = m.group(1)
    if 'max_batch_size:' in text:
        m = re.search(r'max_batch_size:\s*(\d+)', text)
        if m: out['max_batch_size'] = int(m.group(1))
    out['inputs'] = re.findall(r'input\s*\[', text)
    out['outputs'] = re.findall(r'output\s*\[', text)
    return out


def inspect_model(model_dir: pathlib.Path) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    versions = [p.name for p in model_dir.iterdir() if p.is_dir() and NUMERIC_VERSION.match(p.name)] if model_dir.exists() else []
    config = model_dir / 'config.pbtxt'
    custom_configs = list((model_dir / 'configs').glob('*.pbtxt')) if (model_dir / 'configs').is_dir() else []
    info = {'path': str(model_dir), 'versions': versions, 'config': str(config) if config.exists() else None, 'custom_configs': [str(p) for p in custom_configs], 'is_ensemble': False, 'backend': None, 'platform': None, 'max_batch_size': None, 'config_name': None, 'inputs': [], 'outputs': [], 'ignored_version_like_dirs': []}
    for child in model_dir.iterdir() if model_dir.exists() else []:
        if child.is_dir() and not NUMERIC_VERSION.match(child.name) and child.name not in {'configs'}:
            info['ignored_version_like_dirs'].append(child.name)
    if not versions:
        findings.append(Finding('error', model_dir.name, 'model directory has no positive numeric version directories', str(model_dir)))
    if not config.exists() and not custom_configs:
        findings.append(Finding('error', model_dir.name, 'model directory has no config.pbtxt or custom configs', str(model_dir)))
    if config.exists():
        text = config.read_text(errors='ignore')
        parsed = parse_config(text)
        info.update({'backend': parsed.get('backend'), 'platform': parsed.get('platform'), 'max_batch_size': parsed.get('max_batch_size'), 'config_name': model_dir.name, 'inputs': parsed['inputs'], 'outputs': parsed['outputs']})
        if 'name' in parsed and parsed['name'] != model_dir.name:
            findings.append(Finding('error', model_dir.name, f'config name {parsed["name"]!r} does not match directory name {model_dir.name!r}', str(config)))
        if 'backend' not in parsed and 'platform' not in parsed:
            findings.append(Finding('warning', model_dir.name, 'config does not declare backend or platform explicitly', str(config)))
        if 'max_batch_size' not in parsed:
            findings.append(Finding('warning', model_dir.name, 'config does not declare max_batch_size', str(config)))
        if not parsed['inputs']:
            findings.append(Finding('warning', model_dir.name, 'config has no obvious input block markers', str(config)))
        if not parsed['outputs']:
            findings.append(Finding('warning', model_dir.name, 'config has no obvious output block markers', str(config)))
    return info, findings


def validate(repo: pathlib.Path) -> Report:
    findings: list[Finding] = []
    models: list[dict[str, Any]] = []
    if not repo.exists():
        return Report(False, str(repo), {'errors': 1, 'warnings': 0, 'models': 0}, [Finding('error', repo.name or str(repo), 'repository path does not exist', str(repo))], [])
    for model_dir in sorted(p for p in repo.iterdir() if p.is_dir() and not p.name.startswith('.')):
        info, local_findings = inspect_model(model_dir)
        models.append(info)
        findings.extend(local_findings)
    errors = sum(1 for f in findings if f.severity == 'error')
    warnings = sum(1 for f in findings if f.severity == 'warning')
    return Report(errors == 0, str(repo), {'errors': errors, 'warnings': warnings, 'models': len(models)}, findings, models)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-repository', required=True)
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    report = validate(pathlib.Path(a.model_repository))
    if a.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print('Repository:', report.repository)
        print('ok:', report.ok)
        print('summary:', report.summary)
        for finding in report.findings:
            print(f"{finding.severity.upper()} {finding.model}: {finding.message}")
    return 0 if report.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
