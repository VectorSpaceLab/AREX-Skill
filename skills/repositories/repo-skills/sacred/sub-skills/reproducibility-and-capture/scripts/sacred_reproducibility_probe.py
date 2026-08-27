#!/usr/bin/env python3
"""Smoke-test Sacred fixed seeding and explicit stdout capture.

The probe imports the active Sacred installation, builds a tiny experiment,
runs it twice with a fixed root seed, and asserts that the root seed,
per-call captured-function seeds, PRNG-derived values, and captured output are
identical across runs. It avoids optional NumPy/TensorFlow imports; if NumPy is
already installed, Sacred may choose a NumPy RNG internally and the adapter below
handles that.
"""

import json
import random
import sys

try:
    from sacred import Experiment
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Sacred and its runtime dependencies are not importable in this Python. "
        "Install Sacred and ensure setuptools provides pkg_resources, then rerun this probe."
    ) from exc

FIXED_SEED = 314159265


def _rng_int(rng, low=0, high=1_000_000):
    """Return an int from Python, legacy NumPy, or modern NumPy RNGs."""
    if hasattr(rng, "integers"):
        return int(rng.integers(low, high))
    return int(rng.randint(low, high))


def _run_once():
    ex = Experiment("reproducibility_probe", save_git_info=False)

    @ex.capture
    def captured_signal(label, _seed, _rnd):
        value = _rng_int(_rnd)
        print(f"CAPTURE label={label} seed={int(_seed)} value={value}")
        return {"label": label, "seed": int(_seed), "value": value}

    @ex.main
    def main(_run):
        global_draw = random.randint(0, 1_000_000)
        first = captured_signal("first")
        # This consumes the global PRNG to prove the captured-function stream is
        # independent of ordinary global draws within this fixed experiment.
        ignored_global_draw = random.randint(0, 1_000_000)
        second = captured_signal("second")
        print(
            "ROOT seed={} global={} ignored_global={}".format(
                int(_run.config["seed"]), global_draw, ignored_global_draw
            )
        )
        return {
            "root_seed": int(_run.config["seed"]),
            "global_draw": int(global_draw),
            "ignored_global_draw": int(ignored_global_draw),
            "captured": [first, second],
        }

    run = ex.run(
        config_updates={"seed": FIXED_SEED},
        options={"--capture": "sys", "--loglevel": "CRITICAL"},
    )
    return {
        "config_seed": int(run.config["seed"]),
        "result": run.result,
        "captured_out": run.captured_out,
        "status": run.status,
    }


def main():
    first = _run_once()
    second = _run_once()

    assert first["status"] == "COMPLETED", first["status"]
    assert second["status"] == "COMPLETED", second["status"]
    assert first["config_seed"] == FIXED_SEED
    assert second["config_seed"] == FIXED_SEED
    assert first["result"] == second["result"], (first["result"], second["result"])
    assert first["captured_out"] == second["captured_out"], (
        first["captured_out"],
        second["captured_out"],
    )

    captured = first["result"]["captured"]
    assert [item["label"] for item in captured] == ["first", "second"]
    assert captured[0]["seed"] != captured[1]["seed"], captured
    assert "CAPTURE label=first" in first["captured_out"]
    assert "ROOT seed={}".format(FIXED_SEED) in first["captured_out"]

    summary = {
        "ok": True,
        "sacred_seed": FIXED_SEED,
        "captured_function_seeds": [item["seed"] for item in captured],
        "captured_output_lines": first["captured_out"].splitlines(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
