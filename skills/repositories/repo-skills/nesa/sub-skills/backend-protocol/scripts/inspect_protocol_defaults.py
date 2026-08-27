#!/usr/bin/env python3
"""Self-contained check of Nesa protocol defaults and validation rules."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum
from typing import Optional

_MAX_TEMP = 1e-2
_SAMPLING_EPS = 1e-5


class SamplingType(IntEnum):
    GREEDY = 0
    RANDOM = 1
    RANDOM_SEED = 2


class Role(str, Enum):
    ASSISTANT = "assistant"
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


@dataclass
class LLMParams:
    n: int = 1
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    repetition_penalty: float = 1.0
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = -1
    min_p: float = 0.0
    seed: Optional[int] = None
    stop_token_ids: list[int] = field(default_factory=list)
    ignore_eos: bool = False
    max_tokens: Optional[int] = 16
    min_tokens: int = 0
    skip_special_tokens: bool = True
    detokenize: bool = True
    truncate_prompt_tokens: Optional[int] = None

    def __post_init__(self) -> None:
        if 0 < self.temperature < _MAX_TEMP:
            self.temperature = max(self.temperature, _MAX_TEMP)
        if self.seed == -1:
            self.seed = None
        self._verify_args()
        if self.temperature < _SAMPLING_EPS:
            self.top_p = 1.0
            self.top_k = -1
            self.min_p = 0.0
            self._verify_greedy_sampling()

    def _verify_args(self) -> None:
        if not isinstance(self.n, int) or self.n < 1:
            raise ValueError(f"n must be an int at least 1, got {self.n!r}")
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError("presence_penalty must be in [-2, 2]")
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError("frequency_penalty must be in [-2, 2]")
        if not 0.0 < self.repetition_penalty <= 2.0:
            raise ValueError("repetition_penalty must be in (0, 2]")
        if self.temperature < 0.0:
            raise ValueError(f"temperature must be non-negative, got {self.temperature}")
        if not 0.0 < self.top_p <= 1.0:
            raise ValueError("top_p must be in (0, 1]")
        if self.top_k < -1 or self.top_k == 0 or not isinstance(self.top_k, int):
            raise ValueError("top_k must be -1 or an integer at least 1")
        if not 0.0 <= self.min_p <= 1.0:
            raise ValueError("min_p must be in [0, 1]")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if self.min_tokens < 0:
            raise ValueError("min_tokens must be non-negative")
        if self.max_tokens is not None and self.min_tokens > self.max_tokens:
            raise ValueError("min_tokens must be less than or equal to max_tokens")

    def _verify_greedy_sampling(self) -> None:
        if self.n > 1:
            raise ValueError("n must be 1 when using greedy sampling")

    @property
    def sampling_type(self) -> str:
        if self.temperature < _SAMPLING_EPS:
            return SamplingType.GREEDY.name
        if self.seed is not None:
            return SamplingType.RANDOM_SEED.name
        return SamplingType.RANDOM.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Print Nesa protocol defaults and validation examples.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Temperature to validate.")
    parser.add_argument("--n", type=int, default=1, help="Number of completions to validate.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    report = {"roles": [role.value for role in Role], "default_params": asdict(LLMParams())}
    try:
        params = LLMParams(temperature=args.temperature, n=args.n)
        report["requested_params"] = asdict(params)
        report["requested_sampling_type"] = params.sampling_type
        report["ok"] = True
    except Exception as exc:  # noqa: BLE001
        report["requested_error"] = f"{type(exc).__name__}: {exc}"
        report["ok"] = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Roles:", ", ".join(report["roles"]))
        print("Default params:")
        for key, value in report["default_params"].items():
            print(f"- {key}: {value}")
        if report["ok"]:
            print(f"Requested sampling type: {report['requested_sampling_type']}")
        else:
            print(f"Validation error: {report['requested_error']}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
