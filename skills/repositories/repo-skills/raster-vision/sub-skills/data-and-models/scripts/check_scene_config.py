#!/usr/bin/env python3
"""Validate and minimally build a Raster Vision SceneConfig JSON."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any


def read_json_arg(raw_value: str, label: str) -> Any:
    """Read JSON from an inline string or from a local file path."""
    candidate = raw_value[1:] if raw_value.startswith('@') else raw_value
    path = Path(candidate)
    if path.is_file():
        text = path.read_text(encoding='utf-8')
    else:
        text = candidate
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f'{label} must be JSON text or a path to a JSON file: {exc}') from exc


def infer_type_hint(data: dict[str, Any], parent_key: str | None = None) -> str | None:
    keys = set(data)

    if parent_key == 'vector_source':
        return 'geojson_vector_source'
    if parent_key == 'label_source':
        if 'raster_source' in keys:
            return 'semantic_segmentation_label_source'
        if 'vector_source' in keys:
            if any(k in keys for k in (
                    'infer_cells', 'cell_sz', 'background_class_id',
                    'ioa_thresh', 'use_intersection_over_cell',
                    'pick_min_class_id', 'lazy')):
                return 'chip_classification_label_source'
            return 'object_detection_label_source'
    if parent_key == 'label_store':
        if {'vector_output', 'smooth_output', 'smooth_as_uint8', 'rgb'} & keys:
            return 'semantic_segmentation_label_store'
    if parent_key == 'raster_source':
        if 'rasterizer_config' in keys or 'vector_source' in keys:
            return 'rasterized_source'
        if 'uris' in keys:
            return 'rasterio_source'

    if {'train_scenes', 'validation_scenes'} <= keys and 'class_config' in keys:
        return 'dataset'
    if 'id' in keys and 'raster_source' in keys:
        return 'scene'
    if {'vector_source', 'rasterizer_config'} <= keys:
        return 'rasterized_source'
    if 'raster_source' in keys and 'vector_source' not in keys:
        return 'semantic_segmentation_label_source'
    if 'vector_source' in keys and (
            'infer_cells' in keys or 'cell_sz' in keys or
            'background_class_id' in keys or 'ioa_thresh' in keys):
        return 'chip_classification_label_source'
    if 'vector_source' in keys:
        return 'object_detection_label_source'
    if {'vector_output', 'smooth_output', 'smooth_as_uint8', 'rgb'} & keys:
        return 'semantic_segmentation_label_store'
    if 'uris' in keys and (
            'allow_streaming' in keys or 'bbox' in keys or
            'channel_order' in keys or 'transformers' in keys):
        return 'rasterio_source'
    if 'names' in keys and 'train_scenes' not in keys and 'raster_source' not in keys:
        return 'class_config'
    return None


def ensure_type_hints(value: Any, parent_key: str | None = None) -> Any:
    """Recursively add missing type hints for common Raster Vision configs."""
    if isinstance(value, list):
        return [ensure_type_hints(item, parent_key=parent_key) for item in value]
    if not isinstance(value, dict):
        return value

    out = {
        key: ensure_type_hints(val, parent_key=key)
        for key, val in value.items()
    }
    if 'type_hint' not in out:
        inferred = infer_type_hint(out, parent_key=parent_key)
        if inferred is not None:
            out['type_hint'] = inferred

    # Apply scene-aware label-store inference after the child hints exist.
    if out.get('type_hint') == 'scene':
        label_source = out.get('label_source')
        label_store = out.get('label_store')
        label_source_hint = None
        if isinstance(label_source, dict):
            label_source_hint = label_source.get('type_hint')
        if isinstance(label_store, dict) and 'type_hint' not in label_store:
            if label_source_hint == 'semantic_segmentation_label_source':
                label_store['type_hint'] = 'semantic_segmentation_label_store'
            elif label_source_hint == 'object_detection_label_source':
                label_store['type_hint'] = 'object_detection_geojson_store'
            elif label_source_hint == 'chip_classification_label_source':
                label_store['type_hint'] = 'chip_classification_geojson_store'

    return out


def format_exception(exc: Exception) -> list[str]:
    if hasattr(exc, 'errors'):
        try:
            errors = exc.errors()
        except Exception:
            errors = []
        lines: list[str] = []
        for err in errors:
            loc = err.get('loc', ())
            if not isinstance(loc, (tuple, list)):
                loc = (loc, )
            path = '.'.join(str(part) for part in loc)
            msg = err.get('msg', str(exc))
            if path:
                lines.append(f'{path}: {msg}')
            else:
                lines.append(msg)
        if lines:
            return lines
    return [str(exc)]


def print_section(title: str, lines: list[str]) -> None:
    print(title)
    for line in lines:
        print(f'  - {line}')


def structural_scene_check(scene_cfg_data: Any,
                           class_cfg_data: Any | None) -> list[str]:
    issues: list[str] = []

    if not isinstance(scene_cfg_data, dict):
        return ['SceneConfig root must be a JSON object.']

    if 'id' not in scene_cfg_data:
        issues.append('id: required field is missing.')
    if 'raster_source' not in scene_cfg_data:
        issues.append('raster_source: required field is missing.')

    raster_source = scene_cfg_data.get('raster_source')
    if isinstance(raster_source, dict):
        rs_keys = set(raster_source)
        rs_hint = raster_source.get('type_hint')
        if rs_hint == 'rasterized_source' or 'rasterizer_config' in rs_keys:
            if 'vector_source' not in rs_keys:
                issues.append('raster_source.vector_source: required.')
            if 'rasterizer_config' not in rs_keys:
                issues.append('raster_source.rasterizer_config: required.')
        elif rs_hint == 'rasterio_source' or ('uris' in rs_keys and 'vector_source' not in rs_keys):
            if 'uris' not in rs_keys:
                issues.append('raster_source.uris: required for rasterio_source configs.')
    elif 'raster_source' in scene_cfg_data:
        issues.append('raster_source: must be a JSON object.')

    label_source = scene_cfg_data.get('label_source')
    label_source_hint = None
    if isinstance(label_source, dict):
        label_source_hint = label_source.get('type_hint')
        ls_keys = set(label_source)
        if label_source_hint == 'semantic_segmentation_label_source' or 'raster_source' in ls_keys:
            if 'raster_source' not in ls_keys:
                issues.append('label_source.raster_source: required.')
        elif (label_source_hint in {'object_detection_label_source',
                                   'chip_classification_label_source'}
              or 'vector_source' in ls_keys):
            if 'vector_source' not in ls_keys:
                issues.append('label_source.vector_source: required.')
        if (label_source_hint == 'chip_classification_label_source'
                or 'infer_cells' in ls_keys):
            if label_source.get('infer_cells') and label_source.get(
                    'background_class_id') is None:
                issues.append(
                    'label_source.background_class_id: required when infer_cells=True.'
                )
            if label_source.get('infer_cells') and label_source.get('cell_sz') is None:
                issues.append(
                    'label_source.cell_sz: required when infer_cells=True unless the surrounding pipeline fills it.'
                )
    elif label_source is not None:
        issues.append('label_source: must be a JSON object or null.')

    label_store = scene_cfg_data.get('label_store')
    if isinstance(label_store, dict):
        label_store_hint = label_store.get('type_hint')
        ls_keys = set(label_store)
        # These stores often allow auto-generated URIs, so only check for the
        # obvious structural shape here.
        if label_store_hint == 'semantic_segmentation_label_store' or (
                {'smooth_output', 'rgb', 'vector_output'} & ls_keys):
            pass
        elif label_store_hint in {
                'object_detection_geojson_store', 'chip_classification_geojson_store'
        }:
            pass
        elif 'uri' not in ls_keys and label_store.get('uri') is None:
            issues.append('label_store.uri: missing and no type_hint was available to infer the store shape.')
    elif label_store is not None:
        issues.append('label_store: must be a JSON object or null.')

    if isinstance(class_cfg_data, dict):
        names = class_cfg_data.get('names')
        colors = class_cfg_data.get('colors')
        if not isinstance(names, list) or len(names) == 0:
            issues.append('class_config.names: must be a non-empty list.')
        if colors is not None and isinstance(names, list) and len(colors) != len(names):
            issues.append('class_config.colors: length must match class_config.names.')
        null_class = class_cfg_data.get('null_class')
        if null_class is not None and isinstance(names, list) and null_class not in names:
            issues.append('class_config.null_class: must be one of class_config.names.')

    if (label_source is not None or label_store is not None) and class_cfg_data is None:
        issues.append(
            'Build requires --class-config-json because this scene carries labels or a label store.'
        )

    return issues


def runtime_check(scene_cfg_data: Any,
                  class_cfg_data: Any | None) -> tuple[bool, list[str]]:
    try:
        from rastervision.pipeline.config import build_config
        from rastervision.core.data import ClassConfig
    except Exception as exc:
        return False, [
            'Raster Vision is not importable in this environment. Install Raster Vision or set PYTHONPATH so the package can be imported, then rerun this checker.',
            f'Import error: {exc}',
        ]

    try:
        scene_cfg = build_config(scene_cfg_data)
        if hasattr(scene_cfg, 'update'):
            scene_cfg.update()
    except Exception as exc:
        return False, format_exception(exc)

    print('SceneConfig parsed successfully.')
    print(f'  - scene id: {getattr(scene_cfg, "id", "<unknown>")}')
    print(
        f'  - label source: {type(scene_cfg.label_source).__name__ if getattr(scene_cfg, "label_source", None) is not None else "None"}'
    )
    print(
        f'  - label store: {type(scene_cfg.label_store).__name__ if getattr(scene_cfg, "label_store", None) is not None else "None"}'
    )
    print(f'  - AOIs: {len(getattr(scene_cfg, "aoi_uris", []) or [])}')

    should_build = class_cfg_data is not None or (
        getattr(scene_cfg, 'label_source', None) is None and
        getattr(scene_cfg, 'label_store', None) is None)

    if not should_build:
        return True, [
            'Build skipped: this SceneConfig has a label source or label store, so provide --class-config-json to build it.'
        ]

    if class_cfg_data is None:
        class_cfg = ClassConfig(names=['placeholder'])
        print(
            'Build note: no --class-config-json was provided, so this script used a synthetic one-class ClassConfig to validate the imagery-only scene path.'
        )
    else:
        try:
            class_cfg = build_config(class_cfg_data)
        except Exception as exc:
            return False, format_exception(exc)

    try:
        with tempfile.TemporaryDirectory(prefix='rv-scene-check-') as tmp_dir:
            scene = scene_cfg.build(class_cfg, tmp_dir)
    except Exception as exc:
        return False, format_exception(exc)

    print('SceneConfig build succeeded.')
    print(f'  - runtime scene id: {scene.id}')
    print(f'  - raster source: {type(scene.raster_source).__name__}')
    print(
        f'  - label source: {type(scene.label_source).__name__ if scene.label_source is not None else "None"}'
    )
    print(
        f'  - label store: {type(scene.label_store).__name__ if scene.label_store is not None else "None"}'
    )
    print(f'  - AOI polygons: {len(scene.aoi_polygons)}')
    print(f'  - extent: {scene.extent}')
    return True, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Validate and minimally build a Raster Vision SceneConfig JSON.'
    )
    parser.add_argument(
        '--scene-config-json',
        required=True,
        help='SceneConfig JSON text or a path to a JSON file.')
    parser.add_argument(
        '--class-config-json',
        help='Optional ClassConfig JSON text or a path to a JSON file.')
    args = parser.parse_args(argv)

    try:
        scene_cfg_data = ensure_type_hints(
            read_json_arg(args.scene_config_json, 'SceneConfig'))
    except Exception as exc:
        print_section('SceneConfig input error:', format_exception(exc))
        return 2

    class_cfg_data = None
    if args.class_config_json is not None:
        try:
            class_cfg_data = ensure_type_hints(
                read_json_arg(args.class_config_json, 'ClassConfig'))
        except Exception as exc:
            print_section('ClassConfig input error:', format_exception(exc))
            return 2

    runtime_ok, runtime_lines = runtime_check(scene_cfg_data, class_cfg_data)
    if runtime_ok:
        if runtime_lines:
            print_section('SceneConfig check:', runtime_lines)
        return 0

    if runtime_lines and runtime_lines[0].startswith(
            'Raster Vision is not importable'):
        print_section('Environment warning:', runtime_lines)

        structural_issues = structural_scene_check(scene_cfg_data,
                                                  class_cfg_data)
        if structural_issues:
            print_section('Structural issues:', structural_issues)
            return 1

        if class_cfg_data is None and (
                isinstance(scene_cfg_data, dict)
                and (scene_cfg_data.get('label_source') is not None
                     or scene_cfg_data.get('label_store') is not None)):
            print(
                'SceneConfig parsed successfully, but a real Raster Vision installation is required to build label-bearing scenes.'
            )
        else:
            print(
                'SceneConfig structural checks passed, but runtime build was skipped because Raster Vision is not importable in this environment.'
            )
        return 0

    print_section('SceneConfig validation failed:', runtime_lines)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
