#!/usr/bin/env python3
"""Check that a Kubeflow Pipelines environment is usable.

This helper intentionally stays light-weight and avoids the original source
checkout. It checks the public import surface, reports installed versions, and
can optionally probe CLI help or compile a tiny pipeline.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Check the installed Kubeflow Pipelines environment.',
    )
    parser.add_argument(
        '--require-kubernetes',
        action='store_true',
        help='Require that kfp.kubernetes imports successfully.',
    )
    parser.add_argument(
        '--probe-cli',
        action='store_true',
        help='Run safe CLI help probes for the installed kfp command if present.',
    )
    parser.add_argument(
        '--probe-compile',
        action='store_true',
        help='Compile a tiny pipeline to a temporary YAML file.',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Write the tiny compiled pipeline here when --probe-compile is set.',
    )
    return parser


def _import_versions(require_kubernetes: bool) -> dict:
    import importlib.metadata as metadata

    import kfp
    from kfp import compiler
    from kfp import dsl
    from kfp import local

    info = {
        'kfp_version': kfp.__version__,
        'kfp_distribution': metadata.version('kfp'),
        'has_dsl': hasattr(kfp, 'dsl'),
        'has_components': hasattr(kfp, 'components'),
        'has_client': hasattr(kfp, 'Client'),
        'compiler_compile_signature': str(compiler.Compiler.compile),
        'dsl_component_signature': str(dsl.component),
        'dsl_pipeline_signature': str(dsl.pipeline),
        'local_init_signature': str(local.init),
    }

    try:
        from kfp.pipeline_spec import pipeline_spec_pb2  # noqa: F401

        info['pipeline_spec_import'] = 'ok'
    except Exception as exc:  # pragma: no cover - diagnostic path
        info['pipeline_spec_import'] = f'failed: {exc}'

    if require_kubernetes:
        from kfp import kubernetes

        info['kubernetes_version'] = getattr(kubernetes, '__version__', 'unknown')
        info['kubernetes_helpers'] = list(kubernetes.__all__)

    return info


def _compile_smoke(output_path: Path | None) -> str:
    from kfp import compiler
    from kfp import dsl

    @dsl.component(base_image='python:3.11')
    def echo(message: str):
        print(message)

    @dsl.pipeline(name='kfp-environment-check')
    def pipeline(message: str = 'hello from KFP'):
        echo(message=message)

    if output_path is None:
        temp_dir = Path(tempfile.mkdtemp(prefix='kfp-env-check-'))
        output_path = temp_dir / 'pipeline.yaml'
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    compiler.Compiler().compile(pipeline, str(output_path))
    return str(output_path)


def _probe_cli() -> dict:
    results = {}
    kfp_cmd = shutil.which('kfp')
    dsl_compile_cmd = shutil.which('dsl-compile')
    results['kfp_command'] = kfp_cmd or 'missing'
    results['dsl_compile_command'] = dsl_compile_cmd or 'missing'

    if kfp_cmd:
        for args, label in (
            ([kfp_cmd, '--help'], 'kfp_help'),
            ([kfp_cmd, 'component', '--help'], 'kfp_component_help'),
            ([kfp_cmd, 'dsl', 'compile', '--help'], 'kfp_dsl_compile_help'),
        ):
            completed = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            results[label] = {
                'returncode': completed.returncode,
                'stdout_head': completed.stdout.splitlines()[:5],
                'stderr_head': completed.stderr.splitlines()[:5],
            }
    return results


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        info = _import_versions(args.require_kubernetes)
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(json.dumps({'status': 'import-failed', 'error': str(exc)}, indent=2))
        return 1

    if args.probe_compile:
        try:
            info['compile_output'] = _compile_smoke(args.output)
        except Exception as exc:  # pragma: no cover - diagnostic path
            info['compile_error'] = str(exc)
            print(json.dumps({'status': 'compile-failed', 'details': info}, indent=2))
            return 1

    if args.probe_cli:
        try:
            info['cli'] = _probe_cli()
        except Exception as exc:  # pragma: no cover - diagnostic path
            info['cli_error'] = str(exc)
            print(json.dumps({'status': 'cli-failed', 'details': info}, indent=2))
            return 1

    print(json.dumps({'status': 'ok', 'details': info}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
