#!/usr/bin/env python
"""Print a fully resolved MMGeneration config.

Safe usage:
- Requires only a config path and optional MMCV-style overrides.
- Does not train, evaluate, or download assets.

Example:
    python print_config.py configs/styleganv2/stylegan2_c2_ffhq_256_b4x8_800k.py \
        --cfg-options model.generator.out_size=512
"""

from __future__ import annotations

import argparse

from mmcv import Config, DictAction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Print the whole config')
    parser.add_argument('config', help='config file path')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        help=('override some settings in the used config, the key-value pair '
              'in xxx=yyy format will be merged into config file. If the '
              'value to be overwritten is a list, it should be like '
              'key="[a,b]" or key=a,b. It also allows nested list/tuple '
              'values, e.g. key="[(a,b),(c,d)]". Note that quotation marks '
              'are necessary and no white space is allowed.'))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = Config.fromfile(args.config)
    if args.cfg_options is not None:
        cfg.merge_from_dict(args.cfg_options)
    if cfg.get('custom_imports', None):
        from mmcv.utils import import_modules_from_strings
        import_modules_from_strings(**cfg['custom_imports'])
    print(f'Config:\n{cfg.pretty_text}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
