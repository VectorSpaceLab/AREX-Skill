#!/usr/bin/env python3
"""Smoke-test the installed xTuring API contract with a dummy in-memory model."""

from __future__ import annotations

try:
    from fastapi.testclient import TestClient
except Exception as exc:  # pragma: no cover - dependency failure is explicit
    raise SystemExit(f"fastapi test client is unavailable: {exc}") from exc

try:
    from xturing.cli import api as api_module
except Exception as exc:  # pragma: no cover - dependency failure is explicit
    raise SystemExit(
        "could not import xturing.cli.api; install xTuring in the active Python "
        f"environment before running this smoke: {exc}"
    ) from exc


class _DummyGenerationConfig:
    def __init__(self) -> None:
        self.penalty_alpha = None
        self.top_k = None
        self.top_p = None
        self.do_sample = None
        self.max_new_tokens = None


class _DummyModel:
    model_name = "dummy-model"

    def __init__(self) -> None:
        self._config = _DummyGenerationConfig()
        self.last_texts: list[str] = []

    def generation_config(self):
        return self._config

    def generate(self, texts):
        self.last_texts = list(texts)
        return [f"echo:{text}" for text in texts]


def _client_with_model():
    api_module.model = _DummyModel()
    return TestClient(api_module.app), api_module.model


def _assert_contains(response_text: str, needle: str) -> None:
    assert needle in response_text, f"expected to find {needle!r} in response body"


def main() -> int:
    client, loaded_model = _client_with_model()

    health = client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json() == {"success": True, "message": "API server is running"}

    legacy = client.post(
        "/api",
        json={
            "prompt": ["hello", "world"],
            "params": {
                "penalty_alpha": 0.3,
                "top_k": 12,
                "top_p": 0.8,
                "do_sample": True,
                "max_new_tokens": 16,
            },
        },
    )
    assert legacy.status_code == 200, legacy.text
    legacy_payload = legacy.json()
    assert legacy_payload["success"] is True
    assert legacy_payload["response"] == ["echo:hello", "echo:world"]
    assert loaded_model.last_texts == ["hello", "world"]
    assert loaded_model._config.penalty_alpha == 0.3
    assert loaded_model._config.top_k == 12
    assert loaded_model._config.top_p == 0.8
    assert loaded_model._config.do_sample is True
    assert loaded_model._config.max_new_tokens == 16

    models = client.get("/v1/models")
    assert models.status_code == 200, models.text
    models_payload = models.json()
    assert models_payload["object"] == "list"
    assert models_payload["data"][0]["id"] == "dummy-model"

    chat = client.post(
        "/v1/chat/completions",
        json={
            "model": "dummy-model",
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Say hi"},
            ],
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 32,
        },
    )
    assert chat.status_code == 200, chat.text
    chat_payload = chat.json()
    assert chat_payload["object"] == "chat.completion"
    assert chat_payload["model"] == "dummy-model"
    assert chat_payload["choices"][0]["message"]["role"] == "assistant"
    assert chat_payload["choices"][0]["message"]["content"] == "echo:system: Be concise.\nuser: Say hi"
    assert chat_payload["usage"]["total_tokens"] >= chat_payload["usage"]["prompt_tokens"]
    assert loaded_model.last_texts == ["system: Be concise.\nuser: Say hi"]
    assert loaded_model._config.penalty_alpha is None
    assert loaded_model._config.top_p == 0.9
    assert loaded_model._config.do_sample is True
    assert loaded_model._config.max_new_tokens == 32

    chat_empty = client.post("/v1/chat/completions", json={"messages": []})
    assert chat_empty.status_code == 400, chat_empty.text
    _assert_contains(chat_empty.text, "messages must not be empty")

    chat_stream = client.post(
        "/v1/chat/completions",
        json={
            "model": "dummy-model",
            "messages": [{"role": "user", "content": "stream me"}],
            "stream": True,
        },
    )
    assert chat_stream.status_code == 200, chat_stream.text
    assert chat_stream.headers["content-type"].startswith("text/event-stream")
    _assert_contains(chat_stream.text, "chat.completion.chunk")
    _assert_contains(chat_stream.text, "data: [DONE]")

    text = client.post(
        "/v1/completions",
        json={
            "model": "dummy-model",
            "prompt": ["hello", "world"],
            "max_tokens": 32,
        },
    )
    assert text.status_code == 200, text.text
    text_payload = text.json()
    assert text_payload["object"] == "text_completion"
    assert len(text_payload["choices"]) == 2
    assert text_payload["choices"][0]["text"] == "echo:hello"
    assert text_payload["choices"][1]["text"] == "echo:world"
    assert text_payload["usage"]["total_tokens"] >= text_payload["usage"]["prompt_tokens"]
    assert loaded_model.last_texts == ["hello", "world"]

    text_stream = client.post(
        "/v1/completions",
        json={
            "model": "dummy-model",
            "prompt": "stream me",
            "stream": True,
        },
    )
    assert text_stream.status_code == 200, text_stream.text
    assert text_stream.headers["content-type"].startswith("text/event-stream")
    _assert_contains(text_stream.text, "text_completion")
    _assert_contains(text_stream.text, "data: [DONE]")

    chat_n = client.post(
        "/v1/chat/completions",
        json={
            "model": "dummy-model",
            "messages": [{"role": "user", "content": "hello"}],
            "n": 2,
        },
    )
    assert chat_n.status_code == 400, chat_n.text
    _assert_contains(chat_n.text, "Only n=1 is currently supported")

    text_n = client.post(
        "/v1/completions",
        json={
            "model": "dummy-model",
            "prompt": "hello",
            "n": 2,
        },
    )
    assert text_n.status_code == 400, text_n.text
    _assert_contains(text_n.text, "Only n=1 is currently supported")

    print("API contract smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
