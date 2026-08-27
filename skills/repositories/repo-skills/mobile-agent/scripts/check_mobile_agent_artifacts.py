#!/usr/bin/env python3
"""Static validation for the generated mobile-agent runtime skill tree."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

MD_LINK=re.compile(r'\[[^\]]+\]\(([^)]+)\)')
NAME_RE=re.compile(r'^name:\s*([a-z0-9][a-z0-9-]{0,63})\s*$', re.M)
DESC_RE=re.compile(r'^description:\s*"[^"]+"\s*$', re.M)
ROLE_RE=re.compile(r'^\s{2}disco-role:\s*operating\s*$', re.M)
DISABLE_RE=re.compile(r'^disable-model-invocation:\s*true\s*$', re.M)


def frontmatter(path: Path) -> str:
    text=path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError('missing opening frontmatter')
    end=text.find('\n---\n',4)
    if end == -1:
        raise ValueError('missing closing frontmatter')
    return text[4:end]


def check_frontmatter(skill_dir: Path, errors: list[str]):
    roots=[skill_dir/'SKILL.md']+sorted((skill_dir/'sub-skills').glob('*/SKILL.md'))
    for p in roots:
        if not p.exists(): errors.append(f'missing {p.relative_to(skill_dir)}'); continue
        try: fm=frontmatter(p)
        except Exception as e: errors.append(f'{p.relative_to(skill_dir)}: {e}'); continue
        name=NAME_RE.search(fm)
        if not name: errors.append(f'{p.relative_to(skill_dir)}: invalid/missing canonical name')
        else:
            expected=skill_dir.name if p.parent==skill_dir else p.parent.name
            if name.group(1)!=expected: errors.append(f'{p.relative_to(skill_dir)}: name {name.group(1)!r} != {expected!r}')
        if not DESC_RE.search(fm): errors.append(f'{p.relative_to(skill_dir)}: description must be double-quoted')
        if not ROLE_RE.search(fm): errors.append(f'{p.relative_to(skill_dir)}: metadata.disco-role operating missing')
        if not DISABLE_RE.search(fm): errors.append(f'{p.relative_to(skill_dir)}: disable-model-invocation true missing')


def check_links(skill_dir: Path, errors: list[str]):
    for p in skill_dir.rglob('*.md'):
        text=p.read_text(encoding='utf-8')
        for link in MD_LINK.findall(text):
            target=link.split('#',1)[0].strip()
            if not target or target.startswith(('http://','https://','mailto:')):
                continue
            if target.startswith('/'):
                errors.append(f'{p.relative_to(skill_dir)}: absolute link {target}')
                continue
            resolved=(p.parent/target).resolve()
            try: resolved.relative_to(skill_dir.resolve())
            except ValueError: errors.append(f'{p.relative_to(skill_dir)}: link escapes skill tree: {target}'); continue
            if not resolved.exists(): errors.append(f'{p.relative_to(skill_dir)}: broken link {target}')


def check_privacy(skill_dir: Path, self_path: Path, errors: list[str]):
    private_patterns=['/'+ 'root/', '.disco/agent/envs', 'production_batches/', 'github-repos/', 'skills/tests/']
    secret_regexes=[re.compile(r'(?<![A-Za-z0-9])sk-[A-Za-z0-9]{12,}'), re.compile(r'AKIA[0-9A-Z]{12,}'), re.compile(r'BEGIN PRIVATE KEY')]
    for p in list(skill_dir.rglob('*.md'))+list(skill_dir.rglob('*.json'))+list(skill_dir.rglob('*.py')):
        if p.resolve()==self_path.resolve():
            continue
        text=p.read_text(encoding='utf-8', errors='ignore')
        for pat in private_patterns:
            if pat in text:
                errors.append(f'{p.relative_to(skill_dir)}: private/local path leak pattern {pat!r}')
        if re.search(r'/home/[A-Za-z0-9_.-]+/', text):
            errors.append(f'{p.relative_to(skill_dir)}: private/local path leak pattern /home/<user>/')
        for rx in secret_regexes:
            if rx.search(text) and 'sk-...' not in text:
                errors.append(f'{p.relative_to(skill_dir)}: possible secret pattern {rx.pattern!r}')


def check_required(skill_dir: Path, errors: list[str]):
    required=[
        'SKILL.md','references/repo-provenance.md','references/repo-routing-metadata.json',
        'references/version-and-family-map.md','references/environment-matrix.md','references/troubleshooting.md',
        'scripts/check_prerequisites.py'
    ]
    subskills=['current-gui-owl','benchmarks-and-evaluation','mobile-agent-e','pc-agent','legacy-agents','ui-s1-training']
    for sid in subskills: required.append(f'sub-skills/{sid}/SKILL.md')
    for rel in required:
        if not (skill_dir/rel).exists(): errors.append(f'missing required file {rel}')
    try:
        meta=json.loads((skill_dir/'references/repo-routing-metadata.json').read_text(encoding='utf-8'))
        if skill_dir.name not in meta.get('skills',{}): errors.append('repo-routing-metadata.json missing skills.<skill-id> entry')
    except Exception as e: errors.append(f'invalid repo-routing-metadata.json: {e}')


def check_debris(skill_dir: Path, errors: list[str]):
    for p in skill_dir.rglob('*'):
        if p.name == '__pycache__' or p.suffix in {'.pyc','.pyo'}:
            errors.append(f'generated cache/debris: {p.relative_to(skill_dir)}')


def main():
    p=argparse.ArgumentParser(description='Validate generated mobile-agent skill tree.')
    p.add_argument('--skill-dir', default=str(Path(__file__).resolve().parents[1]))
    p.add_argument('--json', action='store_true')
    a=p.parse_args()
    skill_dir=Path(a.skill_dir).resolve()
    errors=[]
    for fn in [check_required, check_frontmatter, check_links, lambda d,e: check_privacy(d, Path(__file__), e), check_debris]:
        fn(skill_dir, errors)
    result={'skill_dir': str(skill_dir), 'status': 'PASS' if not errors else 'FAIL', 'errors': errors}
    if a.json: print(json.dumps(result, indent=2))
    else:
        print(f"status={result['status']}")
        for err in errors: print('ERROR:', err)
    return 0 if not errors else 2
if __name__=='__main__': raise SystemExit(main())
