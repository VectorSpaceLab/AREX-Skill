#!/usr/bin/env python3
"""Deterministic torchsummary smoke checks for the model-summary-usage skill.

The script defines tiny PyTorch models locally and imports only the public
installed torchsummary API. It performs no downloads and does not depend on the
original repository tests or examples.
"""

from __future__ import annotations

import argparse
import contextlib
import io
from typing import Iterable, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchsummary import summary, summary_string


EXPECTED_SINGLE = (21840, 21840)
EXPECTED_MULTI = (31120, 31120)
EXPECTED_DTYPE = (31120, 31120)


class SingleInputNet(nn.Module):
    """Small MNIST-like CNN with the parameter count used by torchsummary tests."""

    def __init__(self) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d(0.3)
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class MultipleInputNet(nn.Module):
    """Two-branch linear network with two floating-point inputs."""

    def __init__(self) -> None:
        super().__init__()
        self.fc1a = nn.Linear(300, 50)
        self.fc1b = nn.Linear(50, 10)
        self.fc2a = nn.Linear(300, 50)
        self.fc2b = nn.Linear(50, 10)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        x1 = F.relu(self.fc1a(x1))
        x1 = self.fc1b(x1)
        x2 = F.relu(self.fc2a(x2))
        x2 = self.fc2b(x2)
        x = torch.cat((x1, x2), 0)
        return F.log_softmax(x, dim=1)


class MultipleInputNetDifferentDtypes(nn.Module):
    """Two-branch network that accepts float and long synthetic inputs."""

    def __init__(self) -> None:
        super().__init__()
        self.fc1a = nn.Linear(300, 50)
        self.fc1b = nn.Linear(50, 10)
        self.fc2a = nn.Linear(300, 50)
        self.fc2b = nn.Linear(50, 10)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        x1 = F.relu(self.fc1a(x1))
        x1 = self.fc1b(x1)
        # Convert the long branch to floating point without forcing it to CPU.
        x2 = x2.to(device=x1.device, dtype=torch.float32)
        x2 = F.relu(self.fc2a(x2))
        x2 = self.fc2b(x2)
        x = torch.cat((x1, x2), 0)
        return F.log_softmax(x, dim=1)


def as_int(value: object) -> int:
    """Normalize Python ints and scalar tensors to int for assertions."""

    if hasattr(value, "item"):
        return int(value.item())  # type: ignore[union-attr]
    return int(value)  # type: ignore[arg-type]


def normalize_counts(counts: Sequence[object]) -> Tuple[int, int]:
    if len(counts) != 2:
        raise AssertionError(f"expected two count values, received {counts!r}")
    return as_int(counts[0]), as_int(counts[1])


def resolve_device(device_name: str) -> torch.device:
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit(
            f"requested device {device_name!r}, but torch.cuda.is_available() is false"
        )
    return device


def assert_counts(case_name: str, observed: Sequence[object], expected: Tuple[int, int]) -> None:
    normalized = normalize_counts(observed)
    if normalized != expected:
        raise AssertionError(
            f"{case_name}: expected counts {expected}, observed {normalized}"
        )


def run_case(
    case_name: str,
    model: nn.Module,
    input_size: object,
    expected: Tuple[int, int],
    device: torch.device,
    dtypes: Optional[Sequence[type]] = None,
) -> None:
    """Run summary_string and summary for one deterministic case."""

    model = model.to(device)
    model.eval()

    summary_text, counts = summary_string(
        model,
        input_size,
        device=device,
        dtypes=list(dtypes) if dtypes is not None else None,
    )
    assert_counts(case_name, counts, expected)
    if "Total params" not in summary_text or "Trainable params" not in summary_text:
        raise AssertionError(f"{case_name}: summary_string output is missing totals")

    # Verify the printing API without duplicating the full table in stdout.
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        printed_counts = summary(
            model,
            input_size,
            device=device,
            dtypes=list(dtypes) if dtypes is not None else None,
        )
    assert_counts(case_name, printed_counts, expected)
    if "Total params" not in printed.getvalue():
        raise AssertionError(f"{case_name}: summary did not print the totals table")

    print(summary_text)
    total, trainable = normalize_counts(counts)
    print(f"[ok] {case_name}: total_params={total} trainable_params={trainable}")


def selected_cases(case: str) -> Iterable[str]:
    if case == "all":
        return ("single", "multi", "dtype")
    return (case,)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic torchsummary smoke checks for tiny models.",
    )
    parser.add_argument(
        "--case",
        choices=("single", "multi", "dtype", "all"),
        default="all",
        help="smoke case to run: single, multi, dtype, or all (default: all)",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="device for the model and generated torchsummary inputs (default: cpu)",
    )
    args = parser.parse_args()

    torch.manual_seed(0)
    device = resolve_device(args.device)

    for case_name in selected_cases(args.case):
        if case_name == "single":
            run_case(
                case_name="single",
                model=SingleInputNet(),
                input_size=(1, 28, 28),
                expected=EXPECTED_SINGLE,
                device=device,
            )
        elif case_name == "multi":
            run_case(
                case_name="multi",
                model=MultipleInputNet(),
                input_size=[(1, 300), (1, 300)],
                expected=EXPECTED_MULTI,
                device=device,
            )
        elif case_name == "dtype":
            run_case(
                case_name="dtype",
                model=MultipleInputNetDifferentDtypes(),
                input_size=[(1, 300), (1, 300)],
                expected=EXPECTED_DTYPE,
                device=device,
                dtypes=[torch.FloatTensor, torch.LongTensor],
            )
        else:  # pragma: no cover - guarded by argparse choices.
            raise AssertionError(f"unknown case {case_name!r}")


if __name__ == "__main__":
    main()
