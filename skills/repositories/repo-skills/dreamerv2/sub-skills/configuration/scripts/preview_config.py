#!/usr/bin/env python3
"""Preview DreamerV2 preset composition and typed flag overrides safely.

This helper only loads the installed package config and prints the effective
Config. It does not create a logdir, environment, replay, checkpoint, or
TensorBoard writer. Its --configs/--set interface is helper syntax; the
DreamerV2 runner itself uses --configs NAME ... --KEY VALUE.
"""

import argparse
import sys


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      '--configs', nargs='+', default=['defaults'], metavar='NAME',
      help='preset names in application order (helper syntax)')
  parser.add_argument(
      '--set', dest='updates', action='append', default=[], metavar='KEY=VALUE',
      help='repeat for a package flag override (helper syntax)')
  args = parser.parse_args(argv)

  try:
    from dreamerv2 import api

    config = api.defaults
    for name in args.configs:
      if name == 'defaults':
        # The runner starts from defaults, so an explicit defaults name is a
        # no-op here rather than applying the block a second time.
        continue
      if name not in api.configs:
        raise KeyError('Unknown preset: {}'.format(name))
      config = config.update(api.configs[name])

    flag_argv = []
    for update in args.updates:
      if '=' not in update:
        raise ValueError('--set expects KEY=VALUE: {}'.format(update))
      key, value = update.split('=', 1)
      if not key:
        raise ValueError('--set key is empty')
      flag_argv.extend(['--' + key, value])
    if flag_argv:
      config = config.parse_flags(flag_argv)

    print(config)
    print('\nSelected flat values:')
    for key in sorted(config.flat):
      print('{} = {!r} ({})'.format(key, config.flat[key],
                                    type(config.flat[key]).__name__))
    return 0
  except Exception as exc:  # keep this safe preview concise and actionable
    print('{}: {}'.format(type(exc).__name__, exc), file=sys.stderr)
    return 2


if __name__ == '__main__':
  raise SystemExit(main())
