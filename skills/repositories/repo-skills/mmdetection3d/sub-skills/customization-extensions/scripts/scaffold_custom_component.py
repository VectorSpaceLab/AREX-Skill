#!/usr/bin/env python3
"""Safely scaffold MMDetection3D customization templates.

The script only writes when --output-dir is provided. Otherwise it prints a
preview of the files it would create. All files are created strictly inside the
chosen output directory.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import Dict, Iterable, List

_VALID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_module_name(module_name: str) -> List[str]:
    parts = [part for part in module_name.split('.') if part]
    if not parts:
        raise ValueError('module name must not be empty')
    for part in parts:
        if not _VALID_NAME.match(part):
            raise ValueError(
                f'invalid module name segment: {part!r}. Use only Python '
                'identifier characters.')
    return parts


def _safe_target(base_dir: Path, relative: str) -> Path:
    target = (base_dir / relative).resolve()
    base = base_dir.resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(
            f'path traversal detected for target {relative!r}') from exc
    return target


def _render_init(kind: str, component_name: str, dataset_name: str,
                 transform_name: str) -> str:
    imports: List[str] = []
    exports: List[str] = []
    if kind in {'all', 'component'}:
        imports.append(f'from .component import {component_name}')
        exports.append(component_name)
    if kind in {'all', 'dataset'}:
        imports.append(f'from .dataset import {dataset_name}')
        exports.append(dataset_name)
    if kind in {'all', 'transform'}:
        imports.append(f'from .transform import {transform_name}')
        exports.append(transform_name)

    body = '\n'.join(imports)
    all_line = f"__all__ = {exports!r}" if exports else '__all__ = []'
    return dedent(f'''
    """Public entry points for the generated customization package."""

    {body}

    {all_line}
    ''').lstrip()


def _render_component(component_name: str) -> str:
    return dedent(f'''
    """Starter custom model-component template.

    Replace the placeholder logic with the real feature flow for your use case.
    """

    from mmengine.model import BaseModule

    from mmdet3d.registry import MODELS


    @MODELS.register_module()
    class {component_name}(BaseModule):
        """Starter model component template."""

        def __init__(self, in_channels: int = 1, out_channels: int = 1,
                     init_cfg=None) -> None:
            super().__init__(init_cfg=init_cfg)
            self.in_channels = in_channels
            self.out_channels = out_channels

        def forward(self, inputs, *args, **kwargs):
            return inputs
    ''').lstrip()


def _render_dataset(dataset_name: str) -> str:
    return dedent(f'''
    """Starter custom dataset template.

    Fill in METAINFO and parse_ann_info for the target annotation format.
    """

    from __future__ import annotations

    import numpy as np

    from mmdet3d.datasets import Det3DDataset
    from mmdet3d.registry import DATASETS
    from mmdet3d.structures import LiDARInstance3DBoxes


    @DATASETS.register_module()
    class {dataset_name}(Det3DDataset):
        """Starter dataset template."""

        METAINFO = {{'classes': ('ClassA', 'ClassB')}}

        def parse_ann_info(self, info: dict):
            ann_info = super().parse_ann_info(info)
            if ann_info is None:
                return None
            if 'gt_bboxes_3d' in ann_info and not isinstance(
                    ann_info['gt_bboxes_3d'], LiDARInstance3DBoxes):
                boxes = np.asarray(ann_info['gt_bboxes_3d'], dtype=np.float32)
                ann_info['gt_bboxes_3d'] = LiDARInstance3DBoxes(boxes)
            return ann_info
    ''').lstrip()


def _render_transform(transform_name: str) -> str:
    return dedent(f'''
    """Starter custom transform template.

    Keep the transform contract small and explicit.
    """

    from mmcv.transforms import BaseTransform

    from mmdet3d.registry import TRANSFORMS


    @TRANSFORMS.register_module()
    class {transform_name}(BaseTransform):
        """Starter pipeline transform template."""

        def __init__(self, flag_key: str = 'custom_flag',
                     flag_value: bool = True) -> None:
            self.flag_key = flag_key
            self.flag_value = flag_value

        def transform(self, results: dict) -> dict:
            results[self.flag_key] = self.flag_value
            return results
    ''').lstrip()


def _render_config_snippet(module_name: str, component_name: str,
                           dataset_name: str, transform_name: str,
                           kind: str) -> str:
    snippet_lines = [
        'custom_imports = dict(',
        f"    imports={[module_name]!r},",
        '    allow_failed_imports=False)',
        '',
        "default_scope = 'mmdet3d'",
        '',
    ]
    if kind in {'all', 'component'}:
        snippet_lines += [
            'model = dict(',
            f"    backbone=dict(type='{component_name}', in_channels=1, out_channels=1))",
            '',
        ]
    if kind == 'all':
        snippet_lines += [
            f"dataset_type = '{dataset_name}'",
            f"train_pipeline = [dict(type='{transform_name}')]",
            '',
            'train_dataloader = dict(',
            '    dataset=dict(',
            '        type=dataset_type,',
            "        data_root='path/to/data',",
            "        ann_file='path/to/train.pkl',",
            "        data_prefix=dict(pts='points'),",
            '        pipeline=train_pipeline,',
            "        modality=dict(use_lidar=True, use_camera=False),",
            "        metainfo=dict(classes=('ClassA', 'ClassB')),",
            "        box_type_3d='LiDAR'))",
            '',
        ]
    elif kind == 'dataset':
        snippet_lines += [
            f"dataset_type = '{dataset_name}'",
            'train_pipeline = []',
            '',
            'train_dataloader = dict(',
            '    dataset=dict(',
            '        type=dataset_type,',
            "        data_root='path/to/data',",
            "        ann_file='path/to/train.pkl',",
            "        data_prefix=dict(pts='points'),",
            '        pipeline=train_pipeline,',
            "        modality=dict(use_lidar=True, use_camera=False),",
            "        metainfo=dict(classes=('ClassA', 'ClassB')),",
            "        box_type_3d='LiDAR'))",
            '',
        ]
    elif kind == 'transform':
        snippet_lines += [
            f"train_pipeline = [dict(type='{transform_name}')]",
        ]
    return '\n'.join(snippet_lines).rstrip() + '\n'


def _render_preview(file_map: Dict[str, str], module_name: str,
                    output_dir: Path | None) -> str:
    header = [
        'No output directory was provided, so nothing was written.',
        f'Planned module import path: {module_name}',
    ]
    if output_dir is not None:
        header.insert(1, f'Output directory: {output_dir}')
    header.append('Planned files:')
    for rel_path in file_map:
        header.append(f'  - {rel_path}')
    header.append('Pass --output-dir PATH to create these files.')
    return '\n'.join(header) + '\n'


def _build_file_map(module_name: str, component_name: str, dataset_name: str,
                    transform_name: str, kind: str) -> Dict[str, str]:
    file_map: Dict[str, str] = {}
    package_prefix = module_name.replace('.', '/')
    if kind in {'all', 'component', 'dataset', 'transform'}:
        file_map[f'{package_prefix}/__init__.py'] = _render_init(
            kind, component_name, dataset_name, transform_name)
    if kind in {'all', 'component'}:
        file_map[f'{package_prefix}/component.py'] = _render_component(
            component_name)
    if kind in {'all', 'dataset'}:
        file_map[f'{package_prefix}/dataset.py'] = _render_dataset(dataset_name)
    if kind in {'all', 'transform'}:
        file_map[f'{package_prefix}/transform.py'] = _render_transform(
            transform_name)
    file_map['config_snippet.py'] = _render_config_snippet(
        module_name, component_name, dataset_name, transform_name, kind)
    return file_map


def _write_files(base_dir: Path, file_map: Dict[str, str], force: bool) -> None:
    for rel_path, content in file_map.items():
        target = _safe_target(base_dir, rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not force:
            raise FileExistsError(
                f'{target} already exists. Re-run with --force to overwrite.')
        target.write_text(content, encoding='utf-8')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Scaffold MMDetection3D customization templates safely.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Directory that will receive the generated scaffold.')
    parser.add_argument(
        '--module-name',
        default='custom_mmdet3d_extensions',
        help='Importable Python package name for the scaffold.')
    parser.add_argument(
        '--component-name',
        default='CustomComponent',
        help='Class name for the generated model-component template.')
    parser.add_argument(
        '--dataset-name',
        default='CustomDataset',
        help='Class name for the generated dataset template.')
    parser.add_argument(
        '--transform-name',
        default='CustomTransform',
        help='Class name for the generated transform template.')
    parser.add_argument(
        '--kind',
        choices=('all', 'component', 'dataset', 'transform'),
        default='all',
        help='Which template families to generate.')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing files inside the output directory.')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the planned scaffold without writing files.')
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _validate_module_name(args.module_name)
    file_map = _build_file_map(args.module_name, args.component_name,
                               args.dataset_name, args.transform_name,
                               args.kind)

    if args.output_dir is None or args.dry_run:
        sys.stdout.write(_render_preview(file_map, args.module_name,
                                         args.output_dir))
        return 0

    output_dir = args.output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_files(output_dir, file_map, args.force)
    sys.stdout.write(
        f'Wrote {len(file_map)} file(s) under {output_dir.resolve()}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
