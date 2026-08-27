#!/usr/bin/env python3
"""No-download smoke checks for OpenChat ConversationTemplate behavior.

The script uses a deterministic stub tokenizer, so it does not load model
weights or contact model hubs. It verifies role-prefix conditions, EOT placement,
training weights, missing-weight assertions, and system-role handling.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

# When run by file path, Python places this script directory on sys.path rather
# than the caller's working directory. Re-add cwd generically so locally
# available packages can be imported; installed packages still import normally.
cwd = str(Path.cwd())
if cwd not in sys.path:
    sys.path.insert(0, cwd)

try:
    # Importing ochat.config can emit optional training/backend warnings. They
    # are irrelevant to this no-download prompting smoke check.
    with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        warnings.simplefilter("ignore")
        from ochat.config import Conversation, ConversationTemplate, Message
except Exception as exc:  # pragma: no cover - host/package setup failure path
    raise SystemExit(
        "Could not import ochat.config ConversationTemplate. Install ochat in the active Python environment. "
        f"Import error: {exc.__class__.__name__}: {exc}"
    ) from None


@dataclass
class Encoded:
    input_ids: Any


class StubTokenizer:
    """Minimal tokenizer interface needed by ConversationTemplate."""

    is_fast = False

    def __init__(self) -> None:
        self._vocab: dict[str, int] = {"<BOS>": 0}
        self._inverse: dict[int, str] = {0: "<BOS>"}

    def _id(self, token: str) -> int:
        if token not in self._vocab:
            idx = len(self._vocab)
            self._vocab[token] = idx
            self._inverse[idx] = token
        return self._vocab[token]

    def encode_one(self, text: str, *, add_special_tokens: bool = False) -> list[int]:
        if text == "":
            return [self._id("<BOS>")] if add_special_tokens else []
        return [self._id(text)]

    def token_id(self, text: str, *, add_special_tokens: bool = False) -> int:
        ids = self.encode_one(text, add_special_tokens=add_special_tokens)
        if len(ids) != 1:
            raise AssertionError(f"Expected one token for {text!r}, got {ids!r}")
        return ids[0]

    def __call__(self, strings: str | Iterable[str], **kwargs: Any) -> Encoded:
        add_special_tokens = kwargs.get("add_special_tokens", True)
        if isinstance(strings, str):
            return Encoded(self.encode_one(strings, add_special_tokens=add_special_tokens))
        return Encoded([self.encode_one(s, add_special_tokens=add_special_tokens) for s in strings])


def v32_role_prefix(role: str, condition: str) -> str:
    return f"{condition} {role.title()}:".strip()


def openchat36_role_prefix(role: str, condition: str) -> str:
    return "<|start_header_id|>" + f"{condition} {role.title()}".strip() + "<|end_header_id|>\n\n"


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def check_v32_inference_defaults() -> None:
    tok = StubTokenizer()
    template = ConversationTemplate(
        tokenizer=tok,
        role_prefix=v32_role_prefix,
        eot="<|end_of_turn|>",
        inference_condition="GPT4 Correct",
    )
    conv = Conversation(
        items=[Message(role="user", content="ping"), Message(role="assistant", content="")]
    )
    tokens, _ = template.tokenize_conversations([conv], inference=True)
    expected = [
        tok.token_id("", add_special_tokens=True),
        tok.token_id("GPT4 Correct User:"),
        tok.token_id("ping"),
        tok.token_id("<|end_of_turn|>"),
        tok.token_id("GPT4 Correct Assistant:"),
    ]
    assert_equal(tokens[0], expected, "inference default condition and final no-EOT behavior")


def check_custom_condition_override() -> None:
    tok = StubTokenizer()
    template = ConversationTemplate(
        tokenizer=tok,
        role_prefix=v32_role_prefix,
        eot="<|end_of_turn|>",
        inference_condition="GPT4 Correct",
    )
    conv = Conversation(
        condition="Math Correct",
        items=[Message(role="user", content="2+2="), Message(role="assistant", content="")],
    )
    tokens, _ = template.tokenize_conversations([conv], inference=True)
    expected_prefix = tok.token_id("Math Correct User:")
    forbidden_prefix = tok.token_id("GPT4 Correct User:")
    if expected_prefix not in tokens[0] or forbidden_prefix in tokens[0]:
        raise AssertionError("custom condition did not override inference default condition")


def check_training_weights_and_eot() -> None:
    tok = StubTokenizer()
    template = ConversationTemplate(
        tokenizer=tok,
        role_prefix=v32_role_prefix,
        eot="<|end_of_turn|>",
        inference_condition="GPT4 Correct",
    )
    conv = Conversation(
        condition="Math Correct",
        items=[
            Message(role="user", content="question", weight=0.0),
            Message(role="assistant", content="answer", weight=2.0),
        ],
    )
    tokens, weights = template.tokenize_conversations([conv], inference=False, seq_level_weight=True)
    expected_tokens = [
        tok.token_id("", add_special_tokens=True),
        tok.token_id("Math Correct User:"),
        tok.token_id("question"),
        tok.token_id("<|end_of_turn|>"),
        tok.token_id("Math Correct Assistant:"),
        tok.token_id("answer"),
        tok.token_id("<|end_of_turn|>"),
    ]
    expected_weights = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0]
    assert_equal(tokens[0], expected_tokens, "training token sequence")
    assert_equal(weights[0], expected_weights, "training seq-level weights")


def check_missing_training_weight_fails() -> None:
    tok = StubTokenizer()
    template = ConversationTemplate(
        tokenizer=tok,
        role_prefix=v32_role_prefix,
        eot="<|end_of_turn|>",
        inference_condition="GPT4 Correct",
    )
    conv = Conversation(items=[Message(role="assistant", content="answer")])
    try:
        template.tokenize_conversations([conv], inference=False)
    except AssertionError:
        return
    raise AssertionError("non-inference tokenization accepted a message without weight")


def check_openchat36_system_role() -> None:
    tok = StubTokenizer()
    template = ConversationTemplate(
        tokenizer=tok,
        role_prefix=openchat36_role_prefix,
        eot="<|eot_id|>",
        system_as_role=True,
        inference_condition="GPT4 Correct",
    )
    conv = Conversation(
        system="be brief",
        items=[Message(role="user", content="hello"), Message(role="assistant", content="")],
    )
    tokens, weights = template.tokenize_conversations([conv], inference=True)
    expected_tokens = [
        tok.token_id("", add_special_tokens=True),
        tok.token_id("<|start_header_id|>System<|end_header_id|>\n\n"),
        tok.token_id("be brief"),
        tok.token_id("<|eot_id|>"),
        tok.token_id("<|start_header_id|>GPT4 Correct User<|end_header_id|>\n\n"),
        tok.token_id("hello"),
        tok.token_id("<|eot_id|>"),
        tok.token_id("<|start_header_id|>GPT4 Correct Assistant<|end_header_id|>\n\n"),
    ]
    assert_equal(tokens[0], expected_tokens, "OpenChat 3.6 system-role sequence")
    assert_equal(weights[0][:4], [0.0, 0.0, 0.0, 0.0], "system tokens are zero-weighted")


def run_checks(verbose: bool = False) -> None:
    checks = [
        check_v32_inference_defaults,
        check_custom_condition_override,
        check_training_weights_and_eot,
        check_missing_training_weight_fails,
        check_openchat36_system_role,
    ]
    for check in checks:
        check()
        if verbose:
            print(f"ok: {check.__name__}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic no-download smoke checks for OpenChat prompt tokenization."
    )
    parser.add_argument("--verbose", action="store_true", help="Print each passing check.")
    args = parser.parse_args(argv)
    run_checks(verbose=args.verbose)
    if args.verbose:
        print("all prompting smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
