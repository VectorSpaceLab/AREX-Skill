#!/usr/bin/env python3
"""No-network optional provider diagnostic for Pydantic AI.

Usage:
    python check_optional_provider.py openai:gpt-5.2 anthropic google:gemini-3-pro-preview
    python check_optional_provider.py --list

The script checks local Python imports and whether expected environment-variable
names are set. It never sends network requests, validates credentials, or prints
secret values.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ProviderDiagnostic:
    extra: str
    imports: tuple[str, ...]
    env_vars: tuple[str, ...] = ()
    optional_env_vars: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


OPENAI_COMPATIBLE = ProviderDiagnostic(
    extra='openai',
    imports=('openai',),
    notes=('OpenAI-compatible providers usually need provider-specific API keys and may need explicit base URLs.',),
)

PROVIDERS: dict[str, ProviderDiagnostic] = {
    'openai': ProviderDiagnostic('openai', ('openai',), ('OPENAI_API_KEY',), ('OPENAI_BASE_URL',)),
    'openai-chat': ProviderDiagnostic('openai', ('openai',), ('OPENAI_API_KEY',), ('OPENAI_BASE_URL',)),
    'openai-responses': ProviderDiagnostic('openai', ('openai',), ('OPENAI_API_KEY',), ('OPENAI_BASE_URL',)),
    'azure': ProviderDiagnostic(
        'openai',
        ('openai',),
        ('AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY', 'OPENAI_API_VERSION'),
    ),
    'anthropic': ProviderDiagnostic('anthropic', ('anthropic',), ('ANTHROPIC_API_KEY',)),
    'google': ProviderDiagnostic('google', ('google.genai',), ('GOOGLE_API_KEY',), ('GEMINI_API_KEY',)),
    'google-gla': ProviderDiagnostic(
        'google',
        ('google.genai',),
        ('GEMINI_API_KEY',),
        notes=("Deprecated prefix; prefer 'google:'.",),
    ),
    'google-cloud': ProviderDiagnostic(
        'google',
        ('google.genai',),
        (),
        ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION'),
        ('Google Cloud may also use application default credentials that this script cannot inspect.',),
    ),
    'google-vertex': ProviderDiagnostic(
        'google',
        ('google.genai',),
        (),
        ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION'),
        ("Deprecated prefix; prefer 'google-cloud:'.",),
    ),
    'vertexai': ProviderDiagnostic(
        'vertexai',
        ('google.auth', 'requests'),
        (),
        ('GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_LOCATION'),
        ("Legacy alias; prefer 'google-cloud:' for current GoogleModel usage.",),
    ),
    'bedrock': ProviderDiagnostic(
        'bedrock',
        ('boto3',),
        (),
        ('AWS_BEARER_TOKEN_BEDROCK', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_DEFAULT_REGION'),
    ),
    'groq': ProviderDiagnostic('groq', ('groq',), ('GROQ_API_KEY',), ('GROQ_BASE_URL',)),
    'mistral': ProviderDiagnostic('mistral', ('mistralai',), ('MISTRAL_API_KEY',)),
    'cohere': ProviderDiagnostic('cohere', ('cohere',), ('CO_API_KEY',), ('CO_BASE_URL',)),
    'xai': ProviderDiagnostic('xai', ('xai_sdk',), ('XAI_API_KEY',)),
    'grok': ProviderDiagnostic('xai', ('openai',), ('GROK_API_KEY',), notes=("Compatibility path; prefer 'xai:' for new code.",)),
    'huggingface': ProviderDiagnostic('huggingface', ('huggingface_hub',), ('HF_TOKEN',)),
    'ollama': ProviderDiagnostic('openai', ('openai',), ('OLLAMA_BASE_URL',), ('OLLAMA_API_KEY',)),
    'openrouter': ProviderDiagnostic('openrouter', ('openai',), ('OPENROUTER_API_KEY',), ('OPENROUTER_APP_URL', 'OPENROUTER_APP_TITLE')),
    'cerebras': ProviderDiagnostic('openai', ('openai',), ('CEREBRAS_API_KEY',)),
    'deepseek': ProviderDiagnostic('openai', ('openai',), ('DEEPSEEK_API_KEY',)),
    'fireworks': ProviderDiagnostic('openai', ('openai',), ('FIREWORKS_API_KEY',)),
    'github': ProviderDiagnostic('openai', ('openai',), ('GITHUB_API_KEY',)),
    'heroku': ProviderDiagnostic('openai', ('openai',), ('HEROKU_INFERENCE_KEY',), ('HEROKU_INFERENCE_URL',)),
    'litellm': ProviderDiagnostic('openai', ('openai',), notes=('LiteLLM reads provider-specific credentials for the routed backend.',)),
    'moonshotai': ProviderDiagnostic('openai', ('openai',), ('MOONSHOTAI_API_KEY',)),
    'nebius': ProviderDiagnostic('openai', ('openai',), ('NEBIUS_API_KEY',)),
    'ovhcloud': ProviderDiagnostic('openai', ('openai',), ('OVHCLOUD_API_KEY',)),
    'sambanova': ProviderDiagnostic('openai', ('openai',), ('SAMBANOVA_API_KEY',), ('SAMBANOVA_BASE_URL',)),
    'together': ProviderDiagnostic('openai', ('openai',), ('TOGETHER_API_KEY',)),
    'vercel': ProviderDiagnostic('openai', ('openai',), ('VERCEL_AI_GATEWAY_API_KEY',), ('VERCEL_OIDC_TOKEN',)),
    'alibaba': ProviderDiagnostic('openai', ('openai',), ('ALIBABA_API_KEY',), ('DASHSCOPE_API_KEY',)),
    'voyageai': ProviderDiagnostic('voyageai', ('voyageai',), ('VOYAGE_API_KEY',)),
    'sentence-transformers': ProviderDiagnostic('sentence-transformers', ('sentence_transformers',)),
    'duckduckgo': ProviderDiagnostic('duckduckgo', ('ddgs',), notes=('Common tool extra; runtime searches still require network access.',)),
    'web-fetch': ProviderDiagnostic('web-fetch', ('markdownify',), notes=('Common tool extra; runtime fetching still requires network access.',)),
    'tavily': ProviderDiagnostic('tavily', ('tavily',), ('TAVILY_API_KEY',)),
    'exa': ProviderDiagnostic('exa', ('exa_py',), ('EXA_API_KEY',)),
}


EMBEDDING_PROVIDER_ALIASES = {
    'sentence_transformers': 'sentence-transformers',
}


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def env_status(names: Iterable[str]) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for name in names:
        if os.getenv(name):
            present.append(name)
        else:
            missing.append(name)
    return present, missing


def parse_provider(item: str) -> tuple[str, str | None]:
    provider = item.split(':', 1)[0]
    model_name = item.split(':', 1)[1] if ':' in item else None
    if provider.startswith('gateway/'):
        provider = provider.removeprefix('gateway/')
    provider = EMBEDDING_PROVIDER_ALIASES.get(provider, provider)
    return provider, model_name


def known_model_state(item: str) -> str | None:
    if ':' not in item:
        return None
    if not module_available('pydantic_ai'):
        return 'pydantic_ai is not importable, so known_model_names() was not checked'
    try:
        from pydantic_ai.models import known_model_names
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report import blockers.
        return f'known_model_names() unavailable: {type(exc).__name__}: {exc}'
    try:
        known = set(known_model_names())
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report local runtime blockers.
        return f'known_model_names() failed: {type(exc).__name__}: {exc}'
    return 'known to this pydantic_ai build' if item in known else 'not listed by this pydantic_ai build; may still work as a custom provider/model string'


def print_diagnostic(item: str) -> bool:
    provider, model_name = parse_provider(item)
    diagnostic = PROVIDERS.get(provider, OPENAI_COMPATIBLE if provider.startswith('openai-') else None)

    print(f'\n== {item} ==')
    if model_name is not None:
        print(f'provider prefix: {provider}')
        print(f'model name: {model_name}')
    else:
        print(f'provider/tool key: {provider}')

    if diagnostic is None:
        print('status: unknown provider/tool key')
        print('next: instantiate a concrete provider/model class or add a diagnostic mapping for this provider')
        return False

    print(f'smallest documented extra: pydantic-ai-slim[{diagnostic.extra}]')

    imports_ok = True
    for module_name in diagnostic.imports:
        available = module_available(module_name)
        imports_ok = imports_ok and available
        marker = 'ok' if available else 'missing'
        print(f'import {module_name}: {marker}')

    required_present, required_missing = env_status(diagnostic.env_vars)
    optional_present, optional_missing = env_status(diagnostic.optional_env_vars)

    if diagnostic.env_vars:
        print(f'required/env alternatives checked: {", ".join(diagnostic.env_vars)}')
        print(f'env present: {", ".join(required_present) if required_present else "none"}')
        print(f'env missing: {", ".join(required_missing) if required_missing else "none"}')
    if diagnostic.optional_env_vars:
        print(f'optional/env fallback names checked: {", ".join(diagnostic.optional_env_vars)}')
        print(f'optional env present: {", ".join(optional_present) if optional_present else "none"}')

    known_state = known_model_state(item)
    if known_state:
        print(f'known model check: {known_state}')

    for note in diagnostic.notes:
        print(f'note: {note}')

    return imports_ok


def main() -> int:
    parser = argparse.ArgumentParser(description='Check optional Pydantic AI provider imports without network access.')
    parser.add_argument('items', nargs='*', help='Provider keys or provider-prefixed model strings to check.')
    parser.add_argument('--list', action='store_true', help='List known diagnostic keys and exit.')
    args = parser.parse_args()

    if args.list:
        for key in sorted(PROVIDERS):
            print(key)
        return 0

    if not args.items:
        parser.error('provide at least one provider key or provider:model-name string, or use --list')

    all_imports_ok = True
    for item in args.items:
        all_imports_ok = print_diagnostic(item) and all_imports_ok

    return 0 if all_imports_ok else 1


if __name__ == '__main__':
    sys.exit(main())
