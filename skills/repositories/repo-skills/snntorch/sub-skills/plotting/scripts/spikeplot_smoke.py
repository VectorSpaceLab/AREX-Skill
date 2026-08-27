#!/usr/bin/env python3
"""Headless smoke checks for snntorch.spikeplot.

The script uses only synthetic tensors. It reads no datasets and writes no
persistent files. It is intended for CI, SSH, and batch environments where a GUI
backend is unavailable.
"""

from __future__ import annotations

import os
import sys

# Must be set before importing matplotlib.pyplot or snntorch.spikeplot.
os.environ.setdefault("MPLBACKEND", "Agg")


def _import_dependencies():
    try:
        import matplotlib  # type: ignore

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt  # type: ignore
        from matplotlib.animation import ArtistAnimation  # type: ignore
        import torch  # type: ignore
        import snntorch.spikeplot as splt  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user's env
        print(
            "Missing or unusable plotting dependencies. Install snnTorch, torch, "
            "matplotlib, pandas, and the animation writer/display stack required "
            f"by your output format. Import error: {exc}",
            file=sys.stderr,
        )
        return None

    return torch, plt, splt, ArtistAnimation


def _synthetic_spikes(torch, steps: int = 12, outputs: int = 5):
    time = torch.arange(steps, dtype=torch.long).unsqueeze(1)
    neuron = torch.arange(outputs, dtype=torch.long).unsqueeze(0)
    return (((time + 2 * neuron) % 4) == 0).float()


def _synthetic_traces(torch, steps: int = 15, neurons: int = 6):
    time = torch.linspace(0.0, 1.0, steps).unsqueeze(1)
    freqs = torch.arange(1, neurons + 1, dtype=torch.float32).unsqueeze(0)
    phases = torch.arange(neurons, dtype=torch.float32).unsqueeze(0) / 5.0
    traces = torch.sin(6.283185307179586 * (time * freqs / 3.0 + phases))
    overlay = (
        torch.arange(steps, dtype=torch.long).unsqueeze(1)
        % (torch.arange(neurons, dtype=torch.long).unsqueeze(0) + 2)
        == 0
    ).float()
    return traces, overlay


def _synthetic_frames(torch, steps: int = 4, height: int = 3, width: int = 5):
    frames = torch.zeros(steps, height, width)
    for step in range(steps):
        frames[step, step % height, (2 * step) % width] = 1.0
        frames[step, (step + 1) % height, (2 * step + 1) % width] = 0.5
    return frames


def main() -> int:
    deps = _import_dependencies()
    if deps is None:
        return 1
    torch, plt, splt, ArtistAnimation = deps

    try:
        spk = _synthetic_spikes(torch)
        steps, outputs = spk.shape

        fig_raster, ax_raster = plt.subplots(facecolor="w", figsize=(6, 3))
        raster_artist = splt.raster(spk, ax_raster, s=10, c="black")
        raster_points = len(raster_artist.get_offsets())
        expected_points = int(spk.count_nonzero().item())
        assert raster_points == expected_points, (raster_points, expected_points)
        plt.close(fig_raster)

        labels = [f"class-{idx}" for idx in range(outputs)]
        fig_count, ax_count = plt.subplots(facecolor="w", figsize=(7, 4))
        count_result = splt.spike_count(
            spk.detach().cpu(),
            fig_count,
            ax_count,
            labels=labels,
            num_steps=steps,
            time_step=1e-3,
            gridshader=False,
        )
        assert count_result is None
        assert ax_count.get_ylabel() == "Labels"
        assert ax_count.get_xlabel() == "Time [s]"
        plt.close(fig_count)

        traces, overlay = _synthetic_traces(torch)
        fig_traces = plt.figure(facecolor="w", figsize=(8, 4))
        trace_result = splt.traces(
            traces,
            spk=overlay,
            dim=(2, 3),
            spk_height=2.0,
            titles=[f"n{idx}" for idx in range(traces.shape[1])],
        )
        assert trace_result is None
        assert len(fig_traces.axes) == 6
        plt.close(fig_traces)

        frames = _synthetic_frames(torch)
        fig_anim, ax_anim = plt.subplots(facecolor="w", figsize=(4, 3))
        anim = splt.animator(frames, fig_anim, ax_anim, interval=20, cmap="gray")
        assert isinstance(anim, ArtistAnimation)

        # Display rendering is optional because notebook/video writers vary by host.
        jshtml_status = "skipped"
        try:
            jshtml = anim.to_jshtml()
            assert isinstance(jshtml, str) and len(jshtml) > 0
            jshtml_status = "ok"
        except Exception as exc:  # pragma: no cover - depends on writer/display stack
            jshtml_status = f"skipped:{type(exc).__name__}"
        plt.close(fig_anim)

    except Exception as exc:
        plt.close("all")
        print(f"spikeplot smoke failed: {exc}", file=sys.stderr)
        return 1

    print(f"raster points: {raster_points}")
    print(f"spike_count labels: {labels}")
    print(f"traces panels: {len(fig_traces.axes)} with dim=(2, 3)")
    print(f"animator object: {type(anim).__name__}, jshtml={jshtml_status}")
    print("spikeplot smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
