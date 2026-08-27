#!/usr/bin/env python3
"""Check that scikit-plot imports and can render one tiny plot.

This helper is intentionally small and safe: it uses the Agg backend, creates a
2x2 confusion-matrix plot in memory, prints the package version, and exits with
status 0 only when the import and plot both succeed.
"""

from __future__ import annotations

import sys


def _compat_message(exc: BaseException) -> str:
    text = str(exc)
    if "interp" in text and "scipy" in text:
        return (
            "scikitplot failed to import because SciPy is too new for this "
            "0.3.7 snapshot. Install a compatible SciPy, for example: "
            "python -m pip install 'scipy<1.11'"
        )
    if "get_cmap" in text and "matplotlib" in text:
        return (
            "scikitplot failed while plotting because Matplotlib is too new "
            "for this 0.3.7 snapshot. Install a compatible Matplotlib, for "
            "example: python -m pip install 'matplotlib<3.9'"
        )
    return f"scikitplot environment check failed: {exc}"


def main() -> int:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        import scikitplot
        from scikitplot.metrics import plot_confusion_matrix

        fig, ax = plt.subplots(figsize=(3, 3))
        out_ax = plot_confusion_matrix([0, 1], [1, 0], ax=ax)
        if out_ax is not ax:
            raise RuntimeError("plot_confusion_matrix did not return the supplied Axes")
        plt.close(fig)
        print(f"scikitplot {scikitplot.__version__} smoke ok")
        return 0
    except Exception as exc:  # keep the user-facing diagnostic concise
        print(_compat_message(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
