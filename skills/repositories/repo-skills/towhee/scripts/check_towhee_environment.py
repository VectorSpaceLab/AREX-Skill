#!/usr/bin/env python3
"""Safe Towhee environment check for the generated Towhee repo skill.

This helper avoids network, Hub downloads, Docker, Triton, long-running servers,
model downloads, and training. It verifies the public package surfaces that the
root skill routes to most often.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import traceback
from importlib import metadata
from typing import Any


def fail(message: str, *, code: int = 1, details: dict[str, Any] | None = None) -> int:
    payload = {"status": "fail", "message": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    return code


def check_imports(verbose: bool) -> dict[str, Any]:
    try:
        import towhee  # pylint: disable=import-outside-toplevel
        from towhee import AutoConfig, pipe  # pylint: disable=import-outside-toplevel
        from towhee.datacollection.entity import Entity  # pylint: disable=import-outside-toplevel
        from towhee.serve.api_service import APIService  # pylint: disable=import-outside-toplevel
    except Exception as exc:  # pragma: no cover - depends on caller env
        if verbose:
            traceback.print_exc()
        raise RuntimeError(
            "Towhee import failed. Verify the package is installed, pydantic is compatible, "
            "and setuptools still provides pkg_resources for Towhee 1.1.x."
        ) from exc

    version = metadata.version('towhee')
    pipeline = pipe.input('x').map('x', 'y', lambda x: x + 1).output('y')
    result = pipeline(4).get()
    if result != [5]:
        raise RuntimeError(f"pipeline smoke returned {result!r}; expected [5]")

    batch = [row.get() for row in pipeline.batch([1, 2])]
    if batch != [[2], [3]]:
        raise RuntimeError(f"pipeline batch smoke returned {batch!r}; expected [[2], [3]]")

    config = AutoConfig.LocalCPUConfig().config
    if config != {'device': -1}:
        raise RuntimeError(f"LocalCPUConfig returned {config!r}; expected {{'device': -1}}")

    entity = Entity(a=1)
    entity.combine(Entity(b=2))
    if sorted(entity.__dict__) != ['a', 'b']:
        raise RuntimeError('Entity.combine did not mutate the entity as expected')

    service = APIService(desc='smoke')

    @service.api(path='/echo')
    def echo(x: int) -> int:
        return x

    if not service.routers or service.routers[0].path != '/echo':
        raise RuntimeError('APIService route registration failed')

    return {
        'towhee_version': version,
        'pipeline_result': result,
        'batch_result': batch,
        'local_cpu_config': config,
        'entity_keys': sorted(entity.__dict__),
        'api_service_paths': [router.path for router in service.routers],
    }


def check_cli(timeout: float, verbose: bool) -> dict[str, Any]:
    exe = shutil.which('towhee')
    if exe is None:
        return {'status': 'skipped', 'reason': 'towhee console script is not on PATH'}

    checks = [
        ([exe, '--help'], ['init', 'server']),
        ([exe, 'init', '--help'], ['--type', '--dir']),
        ([exe, 'server', '--help'], ['--http-port', '--grpc-port']),
    ]
    results = []
    for cmd, needles in checks:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        output = proc.stdout + proc.stderr
        if verbose:
            print(f"[towhee-env] {' '.join(cmd)} -> {proc.returncode}")
        if proc.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd)} exited {proc.returncode}: {output[:500]}")
        missing = [needle for needle in needles if needle not in output]
        if missing:
            raise RuntimeError(f"{' '.join(cmd)} missing expected text {missing!r}")
        results.append({'command': cmd[1:] or ['--help'], 'status': 'ok'})
    return {'status': 'ok', 'checks': results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run safe Towhee package checks for skill-guided workflows.')
    parser.add_argument('--skip-cli', action='store_true', help='Skip console-script help checks.')
    parser.add_argument('--timeout', type=float, default=10.0, help='Timeout in seconds for each CLI help command.')
    parser.add_argument('--verbose', action='store_true', help='Print additional diagnostic progress.')
    args = parser.parse_args(argv)

    try:
        payload = {
            'status': 'ok',
            'imports': check_imports(args.verbose),
            'cli': {'status': 'skipped', 'reason': '--skip-cli'} if args.skip_cli else check_cli(args.timeout, args.verbose),
        }
    except Exception as exc:  # pragma: no cover - depends on caller env
        if args.verbose:
            traceback.print_exc()
        return fail(str(exc), details={'exception': type(exc).__name__})

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
