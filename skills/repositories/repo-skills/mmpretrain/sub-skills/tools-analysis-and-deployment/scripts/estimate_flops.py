#!/usr/bin/env python3
"""Estimate FLOPs, parameters, and activations for a model or config."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def locate_repo_root() -> Path:
    """Find the repository root that contains the mmpretrain package."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'mmpretrain' / '__init__.py').is_file():
            return parent
    raise RuntimeError(
        'Unable to locate the repository root that contains the mmpretrain '
        'package.')


REPO_ROOT = locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mmengine.analysis import get_model_complexity_info  # noqa: E402
from mmpretrain import get_model  # noqa: E402


def resolve_model_ref(raw: str) -> str:
    """Resolve a config path against the current working directory and repo."""
    candidate = Path(raw).expanduser()
    search_order = [candidate]
    if not candidate.is_absolute():
        search_order = [Path.cwd() / candidate, REPO_ROOT / candidate, candidate]
    for path in search_order:
        if path.exists():
            return str(path.resolve())
    return raw


def parse_shape(shape_values: list[int]) -> tuple[int, int, int]:
    if len(shape_values) == 1:
        return (3, shape_values[0], shape_values[0])
    if len(shape_values) == 2:
        return (3, shape_values[0], shape_values[1])
    raise ValueError('invalid input shape')


def build_analysis_target(model_ref: str):
    model = get_model(resolve_model_ref(model_ref), pretrained=False, device='cpu')
    model.eval()
    if hasattr(model, 'extract_feat'):
        model.forward = model.extract_feat
        return model, 'feature-extraction path'
    if hasattr(model, 'backbone'):
        backbone = model.backbone
        if hasattr(backbone, 'eval'):
            backbone.eval()
        return backbone, 'backbone module'
    raise NotImplementedError(
        'FLOPs counting is not supported for this model because it does not '
        'expose extract_feat or a backbone module.')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Estimate FLOPs and parameters for a model or config.')
    parser.add_argument('model', help='config file path or registered model reference')
    parser.add_argument(
        '--shape', type=int, nargs='+', default=[224, 224], help='input image size')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_shape = parse_shape(args.shape)
    model, target_name = build_analysis_target(args.model)
    analysis_results = get_model_complexity_info(model, input_shape)

    print(f'Analysis target: {target_name}')
    print(analysis_results['out_arch'])
    print(analysis_results['out_table'])
    split_line = '=' * 30
    print(
        f'{split_line}\nInput shape: {input_shape}\n'
        f'Flops: {analysis_results["flops_str"]}\n'
        f'Params: {analysis_results["params_str"]}\n'
        f'Activation: {analysis_results["activations_str"]}\n{split_line}')
    print('!!!Only the backbone network is counted in FLOPs analysis.')
    print('!!!Please be cautious if you use the results in papers. '
          'You may need to check if all ops are supported and verify that the '
          'flops computation is correct.')


if __name__ == '__main__':
    main()
