"""Compatibility shims for running bundled HiFi-GAN source on modern stacks.

The original HiFi-GAN code was written for an older PyTorch/librosa stack. These
helpers patch only process-local APIs used by the bundled entrypoints; they do
not edit source files or change checkpoints/data.
"""

from __future__ import annotations

import functools
import inspect
import sys
import types


def install_torch_dynamo_stub() -> None:
    """Keep older eager-only training code away from torch.compile internals.

    Modern PyTorch optimizers may lazily touch torch._dynamo even when the user
    never calls torch.compile. HiFi-GAN does not rely on Dynamo, so a tiny stub
    is sufficient for smoke/debug runs in modern environments.
    """
    if "torch._dynamo" in sys.modules:
        return

    stub = types.ModuleType("torch._dynamo")

    def disable(fn=None, recursive: bool = True, wrapping: bool = False):  # type: ignore[no-untyped-def]
        if fn is None:
            return lambda wrapped: disable(wrapped, recursive=recursive, wrapping=wrapping)

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return fn(*args, **kwargs)

        return inner

    stub.disable = disable  # type: ignore[attr-defined]
    stub.graph_break = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    stub.is_compiling = lambda: False  # type: ignore[attr-defined]
    stub.mark_dynamic = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    stub.mark_static = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    stub.mark_static_address = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    stub.allow_in_graph = lambda fn=None, *args, **kwargs: fn if fn is not None else (lambda wrapped: wrapped)  # type: ignore[attr-defined]
    stub.disallow_in_graph = lambda fn=None, *args, **kwargs: fn if fn is not None else (lambda wrapped: wrapped)  # type: ignore[attr-defined]
    stub.assume_constant_result = lambda fn=None, *args, **kwargs: fn if fn is not None else (lambda wrapped: wrapped)  # type: ignore[attr-defined]
    stub.reset = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    stub.config = types.SimpleNamespace(suppress_errors=True)
    sys.modules["torch._dynamo"] = stub


def patch_torch_stft() -> None:
    import torch

    original_stft = torch.stft
    if getattr(original_stft, "_hifigan_compat", False):
        return

    try:
        stft_params = inspect.signature(torch.stft).parameters
        supports_return_complex = "return_complex" in stft_params
    except (TypeError, ValueError):
        supports_return_complex = True

    @functools.wraps(original_stft)
    def stft_compat(*args, **kwargs):  # type: ignore[no-untyped-def]
        if supports_return_complex and "return_complex" not in kwargs:
            kwargs["return_complex"] = False
        return original_stft(*args, **kwargs)

    stft_compat._hifigan_compat = True  # type: ignore[attr-defined]
    torch.stft = stft_compat  # type: ignore[assignment]


def patch_librosa_mel() -> None:
    import librosa.filters

    original_mel = librosa.filters.mel
    if getattr(original_mel, "_hifigan_compat", False):
        return

    @functools.wraps(original_mel)
    def mel_compat(*args, **kwargs):  # type: ignore[no-untyped-def]
        if args:
            names = ["sr", "n_fft", "n_mels", "fmin", "fmax"]
            for name, value in zip(names, args):
                kwargs.setdefault(name, value)
            extra = args[len(names):]
            if extra:
                raise TypeError(f"Too many positional arguments for librosa.filters.mel: {len(args)}")
        return original_mel(**kwargs)

    mel_compat._hifigan_compat = True  # type: ignore[attr-defined]
    librosa.filters.mel = mel_compat  # type: ignore[assignment]


def apply_compat_shims(*, training: bool = False) -> None:
    """Apply process-local compatibility shims for bundled entrypoints."""
    if training:
        install_torch_dynamo_stub()
    patch_torch_stft()
    patch_librosa_mel()
