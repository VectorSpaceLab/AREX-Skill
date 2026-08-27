#!/usr/bin/env python3
"""Render safe Xinference client and cURL snippets.

This helper prints templates only. It never makes network calls, downloads
models, or writes files.
"""

from __future__ import annotations

import argparse
import json
from typing import Tuple

FAMILIES = ("chat", "generate", "embedding", "rerank")


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("URL must not be empty")
    return value.rstrip("/")


def build_openai_base_url(endpoint: str, openai_base_url: str | None) -> Tuple[str, str]:
    endpoint = normalize_url(endpoint)
    if openai_base_url is None:
        return endpoint, f"{endpoint}/v1"

    openai_base_url = normalize_url(openai_base_url)
    if not openai_base_url.endswith("/v1"):
        raise ValueError("--openai-base-url must end with /v1")

    derived_endpoint = openai_base_url[: -len("/v1")]
    if derived_endpoint != endpoint:
        raise ValueError(
            "--endpoint and --openai-base-url must describe the same server"
        )
    return endpoint, openai_base_url


def python_snippet(family: str, base_url: str, model_uid: str, api_key: str) -> str:
    if family == "chat":
        lines = [
            "from openai import OpenAI",
            "",
            f'client = OpenAI(base_url="{base_url}", api_key="{api_key}")',
            "response = client.chat.completions.create(",
            f'    model="{model_uid}",',
            "    messages=[",
            '        {"role": "system", "content": "You are a helpful assistant."},',
            '        {"role": "user", "content": "Replace this with your prompt."},',
            "    ],",
            ")",
            "print(response)",
        ]
        return "\n".join(lines)

    if family == "generate":
        lines = [
            "from openai import OpenAI",
            "",
            f'client = OpenAI(base_url="{base_url}", api_key="{api_key}")',
            "response = client.completions.create(",
            f'    model="{model_uid}",',
            '    prompt="Replace this with your prompt.",',
            ")",
            "print(response)",
        ]
        return "\n".join(lines)

    if family == "embedding":
        lines = [
            "from openai import OpenAI",
            "",
            f'client = OpenAI(base_url="{base_url}", api_key="{api_key}")',
            "response = client.embeddings.create(",
            f'    model="{model_uid}",',
            '    input=["Replace this with text to embed."],',
            ")",
            "print(response)",
        ]
        return "\n".join(lines)

    if family == "rerank":
        lines = [
            "import requests",
            "",
            "headers = {",
            '    "Content-Type": "application/json",',
            f'    "Authorization": "Bearer {api_key}",',
            "}",
            "response = requests.post(",
            f'    "{base_url}/rerank",',
            "    headers=headers,",
            "    json={",
            f'        "model": "{model_uid}",',
            '        "query": "Replace this with your query.",',
            '        "documents": ["Document 1", "Document 2"],',
            "    },",
            ")",
            "print(response.json())",
        ]
        return "\n".join(lines)

    raise ValueError(f"Unsupported family: {family}")


def curl_snippet(family: str, base_url: str, model_uid: str, api_key: str) -> str:
    if family == "chat":
        payload = {
            "model": model_uid,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Replace this with your prompt."},
            ],
        }
        endpoint = f"{base_url}/chat/completions"
    elif family == "generate":
        payload = {
            "model": model_uid,
            "prompt": "Replace this with your prompt.",
        }
        endpoint = f"{base_url}/completions"
    elif family == "embedding":
        payload = {
            "model": model_uid,
            "input": ["Replace this with text to embed."],
        }
        endpoint = f"{base_url}/embeddings"
    elif family == "rerank":
        payload = {
            "model": model_uid,
            "query": "Replace this with your query.",
            "documents": ["Document 1", "Document 2"],
        }
        endpoint = f"{base_url}/rerank"
    else:
        raise ValueError(f"Unsupported family: {family}")

    json_payload = json.dumps(payload, indent=2)
    return "\n".join(
        [
            f'curl -X POST "{endpoint}" \\',
            '  -H "Content-Type: application/json" \\',
            f'  -H "Authorization: Bearer {api_key}" \\',
            f"  -d '{json_payload}'",
        ]
    )


def render(family: str, endpoint: str, openai_base_url: str | None, model_uid: str, api_key: str) -> str:
    endpoint, base_url = build_openai_base_url(endpoint, openai_base_url)
    lines = [
        f"# Family: {family}",
        f"Xinference endpoint: {endpoint}",
        f"OpenAI-compatible base URL: {base_url}",
        f"Model UID: {model_uid}",
        "",
        "## Python",
        python_snippet(family, base_url, model_uid, api_key),
        "",
        "## cURL",
        curl_snippet(family, base_url, model_uid, api_key),
        "",
        "# Reminder",
        "Replace MODEL_UID with the UID returned by a successful launch.",
        "This helper prints templates only and never contacts a server.",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render safe Xinference OpenAI-style client snippets.",
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Xinference service endpoint, for example http://127.0.0.1:9997.",
    )
    parser.add_argument(
        "--openai-base-url",
        help="OpenAI-compatible base URL ending in /v1. Defaults to <endpoint>/v1.",
    )
    parser.add_argument(
        "--model-uid",
        required=True,
        help="Launched model UID to place into the request templates.",
    )
    parser.add_argument(
        "--family",
        required=True,
        choices=FAMILIES,
        help="Request family to render.",
    )
    parser.add_argument(
        "--api-key-placeholder",
        default="YOUR_API_KEY",
        help="Placeholder to place into Authorization headers and SDK calls.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        output = render(
            family=args.family,
            endpoint=args.endpoint,
            openai_base_url=args.openai_base_url,
            model_uid=args.model_uid,
            api_key=args.api_key_placeholder,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
