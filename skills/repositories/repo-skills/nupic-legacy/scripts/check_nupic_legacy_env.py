#!/usr/bin/env python
"""Check whether the current Python can run NuPIC legacy workflows.

This helper is intentionally self-contained and does not read a repository
checkout. Run it inside the Python environment that should use NuPIC legacy.
"""
from __future__ import print_function

import argparse
import json
import platform
import sys


def _import_status(module_name):
    try:
        module = __import__(module_name, fromlist=['*'])
        return {
            'ok': True,
            'version': getattr(module, '__version__', None),
            'error': None,
        }
    except Exception as exc:  # pragma: no cover - diagnostic UI
        return {
            'ok': False,
            'version': None,
            'error': '%s: %s' % (exc.__class__.__name__, exc),
        }


def _check_api_smokes(result):
    try:
        import numpy
        from nupic.algorithms.temporal_memory import TemporalMemory
        from nupic.algorithms.spatial_pooler import SpatialPooler
        from nupic.encoders.scalar import ScalarEncoder
        from nupic.frameworks.opf.model_factory import ModelFactory
        from nupic.engine import Network
        from nupic.swarming import permutations_runner

        tm = TemporalMemory(columnDimensions=(8,), cellsPerColumn=2)
        tm.compute([0, 1], learn=True)

        sp = SpatialPooler(inputDimensions=(8,), columnDimensions=(16,),
                           potentialRadius=8, globalInhibition=True,
                           numActiveColumnsPerInhArea=2, seed=1)
        active = numpy.zeros(16, dtype='uint32')
        sp.compute(numpy.array([1, 0, 1, 0, 0, 0, 0, 0], dtype='uint32'),
                   True, active)

        enc = ScalarEncoder(w=21, minval=0, maxval=10, n=50)
        network = Network()

        result['api_smoke'] = {
            'ok': True,
            'temporal_memory_active_cells': len(tm.getActiveCells()),
            'spatial_pooler_active_columns': int(active.sum()),
            'scalar_encoder_width': enc.getWidth(),
            'model_factory': ModelFactory.__name__,
            'network_regions': len(network.regions),
            'swarming_default_action': permutations_runner.DEFAULT_OPTIONS.get('action'),
        }
    except Exception as exc:  # pragma: no cover - diagnostic UI
        result['api_smoke'] = {
            'ok': False,
            'error': '%s: %s' % (exc.__class__.__name__, exc),
        }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Check installed NuPIC legacy runtime imports and tiny APIs.')
    parser.add_argument('--json', action='store_true',
                        help='emit machine-readable JSON')
    parser.add_argument('--allow-python3', action='store_true',
                        help='do not fail only because the current Python is not 2.7')
    parser.add_argument('--skip-api-smoke', action='store_true',
                        help='only check imports; skip tiny API constructions')
    args = parser.parse_args(argv)

    result = {
        'python': {
            'version': sys.version.split()[0],
            'major': sys.version_info[0],
            'minor': sys.version_info[1],
            'platform': platform.platform(),
        },
        'imports': {},
        'warnings': [],
    }

    if sys.version_info[:2] != (2, 7):
        result['warnings'].append(
            'NuPIC legacy workflows are Python 2.7-era; this interpreter is %s.'
            % sys.version.split()[0])

    for module_name in [
        'nupic',
        'numpy',
        'capnp',
        'nupic.bindings.math',
        'nupic.algorithms.temporal_memory',
        'nupic.algorithms.spatial_pooler',
        'nupic.encoders.scalar',
        'nupic.frameworks.opf.model_factory',
        'nupic.engine',
        'nupic.swarming.permutations_runner',
    ]:
        result['imports'][module_name] = _import_status(module_name)

    if not args.skip_api_smoke:
        _check_api_smokes(result)

    failed_imports = [name for name, status in result['imports'].items()
                      if not status['ok']]
    api_failed = (not args.skip_api_smoke and
                  not result.get('api_smoke', {}).get('ok', False))
    python_failed = (sys.version_info[:2] != (2, 7) and not args.allow_python3)
    exit_code = 0
    if failed_imports or api_failed or python_failed:
        exit_code = 1

    result['ok'] = (exit_code == 0)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print('NuPIC legacy environment check: %s' %
              ('PASS' if result['ok'] else 'FAIL'))
        print('python=%s' % result['python']['version'])
        for warning in result['warnings']:
            print('WARNING: %s' % warning)
        for module_name in sorted(result['imports']):
            status = result['imports'][module_name]
            if status['ok']:
                suffix = '' if status['version'] is None else ' %s' % status['version']
                print('OK import %s%s' % (module_name, suffix))
            else:
                print('FAIL import %s: %s' % (module_name, status['error']))
        if 'api_smoke' in result:
            if result['api_smoke'].get('ok'):
                print('OK tiny API smoke')
            else:
                print('FAIL tiny API smoke: %s' % result['api_smoke'].get('error'))

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
