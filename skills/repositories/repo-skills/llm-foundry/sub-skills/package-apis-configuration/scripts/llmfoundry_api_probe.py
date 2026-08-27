#!/usr/bin/env python3
"""Safe LLM Foundry package API probe.

This probe attempts to import the installed `llmfoundry` package, prints public
registry entries, constructs a tiny CPU-safe `MPTConfig`, and reports torch/CUDA
and optional backend/package availability. It never downloads models, builds a
remote tokenizer, initializes training/eval, or contacts external services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys
import traceback
from types import ModuleType
from typing import Any

REGISTRY_GROUPS = [
    'models',
    'dataloaders',
    'callbacks',
    'callbacks_with_config',
    'optimizers',
    'schedulers',
    'algorithms',
    'tokenizers',
    'metrics',
    'loggers',
    'config_transforms',
    'load_planners',
    'save_planners',
    'tp_strategies',
    'norms',
    'fcs',
    'ffns',
    'ffns_with_norm',
    'ffns_with_megablocks',
    'attention_classes',
    'attention_implementations',
    'param_init_fns',
    'module_init_fns',
]

BASE_MODULES = {
    'composer': 'Composer runtime supplied by the mosaicml package',
    'torch': 'PyTorch runtime',
    'transformers': 'Hugging Face Transformers runtime',
    'omegaconf': 'YAML/config runtime',
    'catalogue': 'registry runtime',
}

OPTIONAL_MODULES = {
    'flash_attn': 'flash attention, fused cross entropy, DAIL RoPE, flash padding paths',
    'transformer_engine.pytorch': 'Transformer Engine fc_type=te and te_ln_mlp FFN paths',
    'megablocks': 'MegaBlocks MoE FFN paths',
    'grouped_gemm': 'MegaBlocks grouped GEMM kernels',
    'tiktoken': 'registered tiktoken tokenizer and OpenAI-style tokenization',
    'openai': 'OpenAI and OpenAI-compatible eval API wrappers',
    'peft': 'PEFT/LoRA wrapping for Hugging Face models',
    'bitsandbytes': '8-bit Hugging Face model loading',
    'mcli': 'MosaicML platform CLI/SDK integration',
    'wandb': 'Weights & Biases logger',
    'mlflow': 'MLflow logger/model registry integration',
}

SIGNATURE_OBJECTS = [
    ('llmfoundry.models.mpt', 'MPTConfig'),
    ('llmfoundry.models.mpt', 'MPTForCausalLM'),
    ('llmfoundry.models.mpt', 'ComposerMPTCausalLM'),
    ('llmfoundry.models.hf', 'ComposerHFCausalLM'),
    ('llmfoundry.models.hf', 'ComposerHFT5'),
    ('llmfoundry.optim', 'DecoupledLionW'),
    ('llmfoundry.utils.builders', 'build_tokenizer'),
    ('llmfoundry.utils.builders', 'build_composer_model'),
    ('llmfoundry.utils.builders', 'build_optimizer'),
    ('llmfoundry.utils.builders', 'build_scheduler'),
    ('llmfoundry.utils.builders', 'build_callback'),
    ('llmfoundry.utils.builders', 'build_logger'),
]


def safe_import(module_name: str) -> tuple[bool, str, ModuleType | None]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic probe should report all failures
        return False, f'{type(exc).__name__}: {exc}', None
    version = getattr(module, '__version__', None)
    if version is None:
        dist_guess = module_name.split('.')[0].replace('_', '-')
        try:
            version = importlib.metadata.version(dist_guess)
        except Exception:
            version = 'importable'
    return True, str(version), module


def distribution_version() -> str:
    for dist_name in ('llm-foundry', 'llmfoundry'):
        try:
            return importlib.metadata.version(dist_name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return 'not found in package metadata'


def dependency_status(modules: dict[str, str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for module_name, purpose in modules.items():
        ok, detail, _ = safe_import(module_name)
        out[module_name] = {
            'importable': ok,
            'detail': detail,
            'purpose': purpose,
        }
    return out


def import_llmfoundry() -> tuple[ModuleType | None, dict[str, Any]]:
    try:
        import llmfoundry  # type: ignore
    except Exception as exc:  # noqa: BLE001
        info: dict[str, Any] = {
            'ok': False,
            'error_type': type(exc).__name__,
            'error': str(exc),
            'missing_module': getattr(exc, 'name', None),
            'traceback': ''.join(traceback.format_exception_only(type(exc), exc)).strip(),
        }
        if 'undefined symbol' in str(exc).lower() and 'flash' in str(exc).lower():
            info['hint'] = 'flash-attn appears ABI-incompatible with the active torch/CUDA runtime; reinstall it for this image or remove it for CPU-only inspection.'
        return None, info
    return llmfoundry, {'ok': True, 'version': getattr(llmfoundry, '__version__', 'unknown')}


def collect_registries() -> dict[str, Any]:
    try:
        from llmfoundry import registry  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {'_error': f'{type(exc).__name__}: {exc}'}

    out: dict[str, Any] = {}
    for group in REGISTRY_GROUPS:
        reg = getattr(registry, group, None)
        if reg is None:
            out[group] = '<registry object not present>'
            continue
        try:
            out[group] = sorted(reg.get_all().keys())
        except Exception as exc:  # noqa: BLE001
            out[group] = f'ERROR: {type(exc).__name__}: {exc}'
    return out


def tiny_mpt_config() -> dict[str, Any]:
    try:
        from llmfoundry.models.mpt import MPTConfig  # type: ignore

        cfg = MPTConfig(
            d_model=64,
            n_heads=4,
            n_layers=2,
            max_seq_len=128,
            vocab_size=1024,
            attn_config={
                'attn_impl': 'torch',
                'attn_type': 'multihead_attention',
            },
            ffn_config={'ffn_type': 'mptmlp'},
            init_config={'name': 'kaiming_normal_'},
            fc_type='torch',
        )
        return {
            'ok': True,
            'model_type': cfg.model_type,
            'd_model': cfg.d_model,
            'n_heads': cfg.n_heads,
            'n_layers': cfg.n_layers,
            'max_seq_len': cfg.max_seq_len,
            'attn_impl': cfg.attn_config.get('attn_impl'),
            'attn_type': cfg.attn_config.get('attn_type'),
            'ffn_type': cfg.ffn_config.get('ffn_type'),
            'fc_type': cfg.fc_type,
            'tie_word_embeddings': cfg.tie_word_embeddings,
        }
    except Exception as exc:  # noqa: BLE001
        return {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}


def torch_status() -> dict[str, Any]:
    ok, detail, module = safe_import('torch')
    if not ok or module is None:
        return {'importable': False, 'error': detail}
    torch = module
    out: dict[str, Any] = {
        'importable': True,
        'version': getattr(torch, '__version__', 'unknown'),
        'cuda_runtime': getattr(torch.version, 'cuda', None),
    }
    try:
        out['cuda_available'] = bool(torch.cuda.is_available())
        out['cuda_device_count'] = int(torch.cuda.device_count()) if out['cuda_available'] else 0
        if out['cuda_available']:
            out['cuda_device_0'] = torch.cuda.get_device_name(0)
            out['cuda_capability_0'] = torch.cuda.get_device_capability(0)
    except Exception as exc:  # noqa: BLE001
        out['cuda_probe_error'] = f'{type(exc).__name__}: {exc}'
    return out


def signatures() -> dict[str, str]:
    out: dict[str, str] = {}
    for module_name, object_name in SIGNATURE_OBJECTS:
        try:
            module = importlib.import_module(module_name)
            obj = getattr(module, object_name)
            out[object_name] = str(inspect.signature(obj))
        except Exception as exc:  # noqa: BLE001
            out[object_name] = f'<unavailable: {type(exc).__name__}: {exc}>'
    return out


def collect() -> dict[str, Any]:
    llmfoundry, import_info = import_llmfoundry()
    data: dict[str, Any] = {
        'python': sys.version.split()[0],
        'distribution_version': distribution_version(),
        'base_dependencies': dependency_status(BASE_MODULES),
        'llmfoundry_import': import_info,
        'torch': torch_status(),
        'optional_dependencies': dependency_status(OPTIONAL_MODULES),
        'probe_note': 'No downloads, training, evaluation, or remote API calls were run.',
    }
    if llmfoundry is not None:
        data['registries'] = collect_registries()
        data['tiny_mpt_config'] = tiny_mpt_config()
        data['signatures'] = signatures()
    else:
        data['registries'] = '<skipped: llmfoundry import failed>'
        data['tiny_mpt_config'] = '<skipped: llmfoundry import failed>'
        data['signatures'] = '<skipped: llmfoundry import failed>'
    return data


def print_human(data: dict[str, Any]) -> None:
    print('LLM Foundry API probe')
    print(f"python: {data['python']}")
    print(f"distribution_version: {data['distribution_version']}")

    print('\nBase dependencies:')
    for name, item in data['base_dependencies'].items():
        status = 'ok' if item['importable'] else 'missing_or_failed'
        print(f"- {name}: {status} ({item['detail']}; {item['purpose']})")

    print('\nllmfoundry import:')
    import_info = data['llmfoundry_import']
    if import_info.get('ok'):
        print(f"- ok: {import_info.get('version')}")
    else:
        print(f"- failed: {import_info.get('error_type')}: {import_info.get('error')}")
        if import_info.get('missing_module'):
            print(f"- missing_module: {import_info['missing_module']}")
        if import_info.get('hint'):
            print(f"- hint: {import_info['hint']}")

    print('\nRegistry entries:')
    registries = data['registries']
    if isinstance(registries, dict):
        for name, entries in registries.items():
            if isinstance(entries, list):
                value = ', '.join(entries) if entries else '(empty)'
            else:
                value = str(entries)
            print(f'- {name}: {value}')
    else:
        print(f'- {registries}')

    print('\nTiny MPTConfig:')
    mpt = data['tiny_mpt_config']
    if isinstance(mpt, dict):
        for key, value in mpt.items():
            print(f'- {key}: {value}')
    else:
        print(f'- {mpt}')

    print('\nTorch/CUDA:')
    for key, value in data['torch'].items():
        print(f'- {key}: {value}')

    print('\nOptional dependencies:')
    for name, item in data['optional_dependencies'].items():
        status = 'ok' if item['importable'] else 'missing_or_failed'
        print(f"- {name}: {status} ({item['detail']}; {item['purpose']})")

    if isinstance(data.get('signatures'), dict):
        print('\nSelected signatures:')
        for name, sig in data['signatures'].items():
            print(f'- {name}{sig}')

    print(f"\n{data['probe_note']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Safely inspect installed LLM Foundry package APIs.')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON.')
    args = parser.parse_args(argv)

    data = collect()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True, default=str))
    else:
        print_human(data)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
