#!/usr/bin/env python3
"""Safe preflight checks for GeoAI inference workflows.

The script only inspects local files, model references, output paths, and
optional package availability. It does not download models, datasets, or
checkpoints, and it does not write outputs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

VECTOR_EXTENSIONS = {'.geojson', '.gpkg', '.shp', '.fgb', '.json', '.parquet'}
RASTER_EXTENSIONS = {'.tif', '.tiff'}

WORKFLOW_PACKAGES = {
    'auto': ['torch', 'transformers', 'rasterio'],
    'semantic-segmentation': ['torch', 'transformers', 'rasterio'],
    'instance-segmentation': ['torch', 'torchvision', 'rasterio'],
    'object-detection': ['torch', 'torchvision', 'rasterio'],
    'prompt-segmentation': ['torch', 'transformers', 'leafmap', 'rasterio'],
    'rfdetr-detect': ['torch', 'rfdetr', 'torchvision', 'rasterio'],
    'rfdetr-seg': ['torch', 'rfdetr', 'torchvision', 'rasterio'],
    'water': ['torch', 'omniwatermask', 'rasterio'],
    'cloudmask': ['torch', 'omnicloudmask', 'rasterio'],
    'multiclean': ['multiclean', 'rasterio'],
    'super-resolution': ['opensr_model', 'torch', 'rasterio', 'requests', 'omegaconf'],
    'onnx-export': ['torch', 'transformers', 'onnx'],
    'onnx-infer': ['onnxruntime', 'rasterio'],
    'samgeo': ['torch', 'transformers', 'leafmap', 'rasterio'],
}

HF_TASKS = {
    'semantic-segmentation',
    'image-segmentation',
    'universal-segmentation',
    'depth-estimation',
    'mask-generation',
    'object-detection',
    'zero-shot-object-detection',
    'classification',
    'image-classification',
}

def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def classify_reference(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {'kind': 'unset', 'value': None}
    if value.startswith(('http://', 'https://')):
        return {'kind': 'remote-url', 'value': value}
    path = Path(value)
    if path.exists():
        return {'kind': 'local-path', 'value': str(path.resolve())}
    if '/' in value:
        return {'kind': 'remote-id', 'value': value}
    return {'kind': 'symbolic-id', 'value': value}

def parse_int_list(values: Optional[List[int]]) -> List[int]:
    if not values:
        return []
    return [int(v) for v in values]

def choose_device(choice: str) -> Dict[str, Any]:
    result = {'requested': choice, 'resolved': choice, 'available': None, 'note': None}
    if choice == 'auto':
        if not module_available('torch'):
            result['resolved'] = 'cpu'
            result['note'] = 'torch is not installed, so auto resolves to cpu for reporting only.'
            return result
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=FutureWarning, module=r'torch\.cuda.*')
            import torch

        if torch.cuda.is_available():
            result['resolved'] = 'cuda'
            result['available'] = 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            result['resolved'] = 'mps'
            result['available'] = 'mps'
        else:
            result['resolved'] = 'cpu'
            result['available'] = 'cpu'
    elif choice == 'cuda':
        if module_available('torch'):
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=FutureWarning, module=r'torch\.cuda.*')
                import torch
            result['available'] = bool(torch.cuda.is_available())
            if not result['available']:
                result['note'] = 'cuda was requested but torch.cuda.is_available() is false.'
        else:
            result['note'] = 'cuda was requested but torch is not installed.'
    elif choice == 'mps':
        if module_available('torch'):
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=FutureWarning, module=r'torch\.cuda.*')
                import torch
            result['available'] = bool(hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())
            if not result['available']:
                result['note'] = 'mps was requested but torch.backends.mps.is_available() is false.'
        else:
            result['note'] = 'mps was requested but torch is not installed.'
    else:
        result['available'] = True
    return result

def inspect_local_raster(path: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {'path': str(path), 'kind': 'file', 'exists': path.exists()}
    if not path.exists():
        info['error'] = 'missing input file'
        return info
    info['size_bytes'] = path.stat().st_size
    if not module_available('rasterio'):
        info['warning'] = 'rasterio is not installed; raster metadata could not be inspected.'
        return info
    import rasterio

    try:
        with rasterio.open(path) as src:
            info.update(
                {
                    'bands': src.count,
                    'width': src.width,
                    'height': src.height,
                    'crs': str(src.crs) if src.crs else None,
                    'dtype': src.dtypes[0] if src.count else None,
                    'nodata': src.nodata,
                    'driver': src.driver,
                }
            )
    except Exception as exc:  # pragma: no cover - defensive preflight
        info['error'] = f'could not open raster: {exc}'
    return info

def validate_output_extensions(workflow: str, output: Optional[str], vector_output: Optional[str], warnings: List[str], errors: List[str]) -> None:
    if output:
        suffix = Path(output).suffix.lower()
        if workflow == 'onnx-export' and suffix != '.onnx':
            errors.append('onnx-export expects an .onnx output path.')
        elif workflow in {'rfdetr-detect', 'rfdetr-seg'}:
            if suffix not in VECTOR_EXTENSIONS:
                warnings.append(f'rfdetr output extension {suffix!r} is unusual; vector files such as .geojson or .gpkg are expected.')
        elif workflow != 'onnx-export' and suffix and suffix not in RASTER_EXTENSIONS:
            warnings.append(f'output extension {suffix!r} is unusual for {workflow}.')
    if vector_output:
        suffix = Path(vector_output).suffix.lower()
        if suffix not in VECTOR_EXTENSIONS:
            warnings.append(f'vector output extension {suffix!r} is unusual; common choices are .geojson, .gpkg, .shp, .fgb, .json, or .parquet.')

def suggest_route(workflow: str, model: Dict[str, Any], task: Optional[str]) -> str:
    if workflow == 'auto':
        if task:
            if task in HF_TASKS:
                return f'Auto route is valid for task {task!r}; use geoai.auto.AutoGeoModel.from_pretrained(..., task={task!r}).'
            return f'Provided task {task!r} is not one of the geospatially exercised HF tasks; auto may still infer a route from config.'
        return 'Use geoai.auto.AutoGeoModel.from_pretrained(...) when the task is unknown or you want task inference.'
    if workflow == 'semantic-segmentation':
        return 'Use geoai.train.semantic_segmentation for a local checkpoint, or geoai.auto.semantic_segmentation for an HF model ID.'
    if workflow in {'instance-segmentation', 'object-detection'}:
        return 'Use geoai.train.instance_segmentation / object_detection for local checkpoints, or geoai.object_detect.multiclass_detection for NWPU-style detector checkpoints.'
    if workflow == 'prompt-segmentation':
        return 'Use GroundedSAM for text+boxes+masks, CLIPSegmentation for text-only masks, or SamGeo for point/box prompts.'
    if workflow.startswith('rfdetr'):
        return 'Use geoai.rfdetr.rfdetr_detect or rfdetr_segment with an installed rfdetr extra.'
    if workflow == 'water':
        return 'Use geoai.water.segment_water with a 4-band input and an explicit band-order preset or list.'
    if workflow == 'cloudmask':
        return 'Use geoai.tools.cloudmask.predict_cloud_mask_from_raster with explicit red, green, and NIR band indices.'
    if workflow == 'multiclean':
        return 'Use geoai.tools.multiclean.clean_raster or clean_segmentation_mask after the primary segmentation run.'
    if workflow == 'super-resolution':
        return 'Use geoai.tools.sr.super_resolution with exactly four bands in RGB+NIR order.'
    if workflow == 'onnx-export':
        return 'Use geoai.onnx.export_to_onnx on a local checkpoint or HF model that can be resolved without training.'
    if workflow == 'onnx-infer':
        return 'Use geoai.onnx.ONNXGeoModel or onnx_semantic_segmentation / onnx_image_classification on a local .onnx file.'
    if workflow == 'samgeo':
        return 'Use geoai.sam.SamGeo; call set_image() before prompt-mode predict().' 
    return 'Use the matching workflow in the reference docs.'

def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        'workflow': args.workflow,
        'task': args.task,
        'device': choose_device(args.device),
        'inputs': [],
        'model': classify_reference(args.model),
        'output': args.output,
        'vector_output': args.vector_output,
        'packages': {},
        'warnings': [],
        'errors': [],
        'suggestion': None,
    }

    packages = WORKFLOW_PACKAGES[args.workflow]
    report['packages'] = {name: module_available(name) for name in packages}
    missing = [name for name, ok in report['packages'].items() if not ok]
    if missing:
        report['warnings'].append('missing optional packages: ' + ', '.join(missing))

    if args.model is None and args.workflow not in {'water', 'cloudmask', 'multiclean'}:
        report['warnings'].append('no model reference was provided; many inference workflows need a checkpoint or model ID.')

    for raw in args.input:
        if raw.startswith(('http://', 'https://')):
            report['inputs'].append({'path': raw, 'kind': 'url', 'note': 'network access would be required to fetch this input.'})
            continue
        path = Path(raw)
        if not path.exists():
            report['inputs'].append({'path': raw, 'kind': 'missing', 'error': 'input file does not exist'})
            report['errors'].append(f'input not found: {raw}')
            continue
        info = inspect_local_raster(path)
        report['inputs'].append(info)
        if 'error' in info:
            report['errors'].append(f"{raw}: {info['error']}")

    bands = parse_int_list(args.bands)
    if bands:
        if min(bands) < 1:
            report['errors'].append('band indices must be 1-based and positive.')
        if any(b < 1 for b in bands):
            report['errors'].append('band indices must be positive integers.')
        if args.workflow in {'super-resolution', 'water'} and len(bands) != 4:
            report['errors'].append(f'{args.workflow} expects exactly 4 bands when explicit bands are supplied.')

    if args.workflow == 'cloudmask':
        for name, value in [('red', args.red_band), ('green', args.green_band), ('nir', args.nir_band)]:
            if value is not None and value < 1:
                report['errors'].append(f'{name} band must be 1-based and positive.')

    if args.tile_size is not None and args.overlap is not None and args.overlap >= args.tile_size:
        report['errors'].append('overlap must be smaller than tile_size.')
    if args.patch_size is not None and args.patch_overlap is not None and args.patch_overlap >= args.patch_size:
        report['errors'].append('patch_overlap must be smaller than patch_size.')

    if args.output:
        validate_output_extensions(args.workflow, args.output, args.vector_output, report['warnings'], report['errors'])

    local_counts = [info.get('bands') for info in report['inputs'] if isinstance(info, dict) and info.get('bands') is not None]
    if local_counts:
        band_count = local_counts[0]
        if args.num_channels is not None and band_count != args.num_channels:
            report['warnings'].append(f'input has {band_count} bands but num_channels={args.num_channels}; confirm that the checkpoint was trained for that channel count.')
        if args.workflow in {'water', 'super-resolution'} and band_count < 4:
            report['errors'].append(f'{args.workflow} expects at least 4 bands in the source raster.')
        if args.workflow == 'cloudmask' and band_count < 3:
            report['errors'].append('cloudmask expects at least 3 bands in the source raster.')
        if args.workflow == 'onnx-infer' and args.model and Path(args.model).suffix.lower() != '.onnx':
            report['warnings'].append('onnx-infer usually expects a local .onnx model file.')
        if bands and max(bands) > band_count:
            report['errors'].append(f'explicit band selection references band {max(bands)}, but the first raster only has {band_count} bands.')
        if args.workflow == 'cloudmask':
            required_max = max(v for v in [args.red_band or 1, args.green_band or 2, args.nir_band or 3])
            if required_max > band_count:
                report['errors'].append(f'cloudmask band selection references band {required_max}, but the first raster only has {band_count} bands.')

    if args.workflow == 'onnx-export' and args.output and not args.output.lower().endswith('.onnx'):
        report['errors'].append('onnx-export requires an .onnx output path.')

    if report['model']['kind'] == 'remote-id' and args.workflow not in {'water', 'cloudmask', 'multiclean'}:
        report['warnings'].append('model looks like a remote Hugging Face identifier; resolving it would require network or a populated cache.')
    if report['model']['kind'] == 'remote-url':
        report['warnings'].append('model is a URL; no download was attempted during preflight.')

    if args.workflow == 'auto' and args.task and args.task not in HF_TASKS:
        report['warnings'].append(f'task {args.task!r} is not one of the geospatially exercised auto tasks.')

    report['suggestion'] = suggest_route(args.workflow, report['model'], args.task)
    report['status'] = 'fail' if report['errors'] else ('warn' if report['warnings'] else 'ok')
    return report

def format_report(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"Workflow: {report['workflow']}")
    if report.get('task'):
        lines.append(f"Task: {report['task']}")
    lines.append(f"Status: {report['status']}")
    device = report['device']
    lines.append(f"Device: requested={device['requested']} resolved={device['resolved']}")
    if device.get('note'):
        lines.append(f"Device note: {device['note']}")

    if report['inputs']:
        lines.append('Inputs:')
        for item in report['inputs']:
            desc = f"  - {item['path']} [{item['kind']}]"
            if 'bands' in item:
                desc += f" {item['bands']} bands {item.get('width')}x{item.get('height')}"
            if item.get('crs'):
                desc += f" CRS={item['crs']}"
            if item.get('dtype'):
                desc += f" dtype={item['dtype']}"
            if item.get('note'):
                desc += f" ({item['note']})"
            if item.get('error'):
                desc += f" ERROR: {item['error']}"
            lines.append(desc)

    if report['model']['kind'] != 'unset':
        lines.append(f"Model: {report['model']['kind']} = {report['model']['value']}")

    if report['output']:
        lines.append(f"Output: {report['output']}")
    if report['vector_output']:
        lines.append(f"Vector output: {report['vector_output']}")

    if report['packages']:
        lines.append('Packages:')
        for name, ok in report['packages'].items():
            lines.append(f"  - {name}: {'present' if ok else 'missing'}")

    if report['warnings']:
        lines.append('Warnings:')
        for msg in report['warnings']:
            lines.append(f'  - {msg}')
    if report['errors']:
        lines.append('Errors:')
        for msg in report['errors']:
            lines.append(f'  - {msg}')

    if report.get('suggestion'):
        lines.append(f"Suggestion: {report['suggestion']}")
    return "\n".join(lines)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Read-only preflight for GeoAI inference workflows.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='This helper only reports; it does not download models, train, or write outputs.',
    )
    parser.add_argument('--workflow', required=True, choices=sorted(WORKFLOW_PACKAGES), help='Inference family to preflight.')
    parser.add_argument('--input', required=True, nargs='+', help='One or more local input files or URLs.')
    parser.add_argument('--model', help='Local checkpoint path or Hugging Face-style model ID.')
    parser.add_argument('--task', help='HF-style task name for auto routing checks.')
    parser.add_argument('--output', help='Expected output path.')
    parser.add_argument('--vector-output', help='Expected vector output path.')
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda', 'mps'], help='Requested inference device.')
    parser.add_argument('--bands', nargs='*', type=int, help='1-based band indices to validate.')
    parser.add_argument('--tile-size', type=int, default=None, help='Sliding-window tile size.')
    parser.add_argument('--overlap', type=int, default=None, help='Sliding-window overlap.')
    parser.add_argument('--patch-size', type=int, default=None, help='Patch size for patch-based workflows.')
    parser.add_argument('--patch-overlap', type=int, default=None, help='Patch overlap for patch-based workflows.')
    parser.add_argument('--num-channels', type=int, default=None, help='Expected input channel count for the model.')
    parser.add_argument('--num-classes', type=int, default=None, help='Expected class count for the model.')
    parser.add_argument('--red-band', type=int, default=None, help='Red band index for cloudmask checks.')
    parser.add_argument('--green-band', type=int, default=None, help='Green band index for cloudmask checks.')
    parser.add_argument('--nir-band', type=int, default=None, help='NIR band index for cloudmask checks.')
    parser.add_argument('--json', action='store_true', help='Print a JSON report instead of human-readable text.')
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_report(report))
    return 1 if report['errors'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
