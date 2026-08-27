#!/usr/bin/env python3
"""Inspect Mage AI configuration without calling a live model."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect Mage AI configuration.')
    parser.add_argument('--project-path', default='.', help='Mage project path.')
    args = parser.parse_args()

    project_path = Path(args.project_path).expanduser().resolve()
    metadata_path = project_path / 'metadata.yaml'
    metadata = {}
    if metadata_path.exists():
        with metadata_path.open('r', encoding='utf-8') as handle:
            metadata = yaml.safe_load(handle) or {}

    ai_config = metadata.get('ai_config', {})
    mode = ai_config.get('mode', 'open_ai') if isinstance(ai_config, dict) else 'open_ai'
    hugging_face_config = ai_config.get('hugging_face_config', {}) if isinstance(ai_config, dict) else {}

    result = {
        'project_path': str(project_path),
        'metadata_exists': metadata_path.exists(),
        'mode': mode,
        'openai_api_key_present': bool(metadata.get('openai_api_key') or os.getenv('OPENAI_API_KEY')),
        'huggingface_api_present': bool(hugging_face_config.get('huggingface_api') or os.getenv('HUGGINGFACE_API')),
        'huggingface_inference_api_token_present': bool(hugging_face_config.get('huggingface_inference_api_token') or os.getenv('HUGGINGFACE_INFERENCE_API_TOKEN')),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
