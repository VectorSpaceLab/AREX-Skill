# Visualization troubleshooting

## Matplotlib output is unavailable

**Symptom**: `mpl` drawing or plotting fails.

**Cause**: the visualization extra is missing or the environment lacks a usable Matplotlib backend.

**Fix**: install `qiskit[visualization]` and set a headless backend such as `MPLBACKEND=Agg` in automation.

## Graphviz or pydot errors

**Symptom**: DAG, pass-manager, or graph-style drawing fails.

**Cause**: Python `pydot` may be installed but the system Graphviz executable is missing.

**Fix**: install Graphviz at the system/package-manager level and then retry the drawing helper.

## LaTeX output fails

**Symptom**: `latex` drawing fails or image conversion fails.

**Cause**: LaTeX rendering depends on `pylatexenc`, Pillow, `pdflatex`, and `pdftocairo` in addition to Qiskit itself.

**Fix**: use `output="text"` or `output="mpl"` if LaTeX is not necessary, or install the missing system tools.

## Style JSON warnings

**Symptom**: a warning says a style JSON file cannot be found.

**Cause**: the selected style name or style path is not visible to the active environment.

**Fix**: pass an existing style dictionary, correct the style path, or fall back to a built-in style.

## Security and trust boundary

**Symptom**: the task asks to draw untrusted labels or arbitrary user-provided circuits using LaTeX/Graphviz modes.

**Cause**: some visualization paths call external tools and accept user-controlled labels.

**Fix**: use text output or sanitize/approve inputs before using external-tool visualization modes.
