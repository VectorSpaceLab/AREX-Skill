#!/usr/bin/env python3
"""Read-only inspection helper for NVIDIA skills catalog checkouts."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

def parse_frontmatter(path: Path):
    text = path.read_text(encoding='utf-8', errors='replace')
    m = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)', text, re.S)
    if not m or yaml is None:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def has_eval(skill_dir: Path) -> bool:
    if any(skill_dir.rglob('evals.json')):
        return True
    for d in ('evals', 'eval'):
        p = skill_dir / d
        if p.is_dir() and any(p.glob('*.json')):
            return True
    bm = skill_dir / 'benchmark'
    return (bm / 'evals.json').is_file()

def main() -> int:
    ap = argparse.ArgumentParser(description='Inspect NVIDIA skills catalog shape and required artifacts.')
    ap.add_argument('--repo-root', default='.', help='Path to a checkout of github.com/NVIDIA/skills')
    ap.add_argument('--json', action='store_true', help='Emit machine-readable JSON')
    ap.add_argument('--summary', action='store_true', help='Emit concise text summary')
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    skills_dir = root / 'skills'
    skill_dirs = []
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.rglob('SKILL.md')):
            rel = skill_md.relative_to(root).as_posix()
            if rel.startswith('skills/disco/') or rel.startswith('skills/tests/'):
                continue
            skill_dirs.append(skill_md.parent)
    top_level_skill_dirs = sorted(
        p for p in skills_dir.glob('*') if p.is_dir() and p.name not in {'disco', 'tests'}
    ) if skills_dir.is_dir() else []
    components = sorted((root / 'components.d').glob('*.yml')) if (root / 'components.d').is_dir() else []
    plugins = sorted((root / 'plugins.d').glob('*.yml')) if (root / 'plugins.d').is_dir() else []
    missing = []
    names = {}
    for sd in skill_dirs:
        rel = sd.relative_to(root).as_posix()
        fm = parse_frontmatter(sd / 'SKILL.md')
        name = fm.get('name')
        if name:
            names.setdefault(name, []).append(rel)
        for fn in ('skill-card.md','skill.oms.sig','BENCHMARK.md'):
            if not (sd / fn).is_file():
                missing.append({'skill': rel, 'missing': fn})
        if not has_eval(sd):
            missing.append({'skill': rel, 'missing': 'evals.json'})
    duplicate_names = {k:v for k,v in names.items() if len(v) > 1}
    generated = {
        'root_readme': (root / 'README.md').is_file(),
        'skills_sh_json': (root / 'skills.sh.json').is_file(),
        'benchmarks_json': (root / 'benchmarks.json').is_file(),
        'metadata_json': (root / '.github/scripts/marketplace/metadata.json').is_file(),
        'claude_marketplace': (root / '.claude-plugin/marketplace.json').is_file(),
        'codex_marketplace': (root / '.agents/plugins/marketplace.json').is_file(),
        'cursor_marketplace': (root / '.cursor-plugin/marketplace.json').is_file(),
    }
    out = {
        'repo_root': str(root),
        'counts': {
            'skill_md_files': len(skill_dirs),
            'top_level_skill_dirs': len(top_level_skill_dirs),
            'component_yml_files': len(components),
            'plugin_yml_files': len([p for p in plugins if not p.name.startswith('_')]),
        },
        'generated_outputs': generated,
        'artifact_issues': missing,
        'duplicate_skill_names': duplicate_names,
        'warnings': [] if yaml else ['PyYAML unavailable; frontmatter and component YAML parsing was limited.'],
    }
    if args.json or not args.summary:
        print(json.dumps(out, indent=2))
    else:
        print(f"repo: {root}")
        for k, v in out['counts'].items():
            print(f"{k}: {v}")
        print(f"artifact issues: {len(missing)}")
        print(f"duplicate skill names: {len(duplicate_names)}")
        absent = [k for k,v in generated.items() if not v]
        print('missing generated outputs: ' + (', '.join(absent) if absent else 'none'))
    return 1 if missing or duplicate_names else 0
if __name__ == '__main__':
    raise SystemExit(main())
