# ManimML Cross-Cutting Troubleshooting

Use this reference for failures that occur before a task reaches a specific ManimML workflow. For layer-specific or MCMC/decision-tree-specific errors, route to the nearest sub-skill troubleshooting page after the shared environment checks pass.

## Install and import checks

### `ModuleNotFoundError: manim_ml`

Likely causes:

- ManimML is not installed in the active Python environment.
- A scene is being rendered by a different `python`/`manim` executable than the one used to install the package.

Recovery:

```bash
python -m pip install manim_ml
python - <<'PY'
import manim_ml
print("manim_ml import ok")
PY
```

If the user is working from a checkout, editable install is fine for development:

```bash
python -m pip install -e .
```

Do not hard-code a local checkout path into generated scenes.

### Wrong Manim package

ManimML examples assume Manim Community (`from manim import *`). If APIs are missing or scene rendering behaves unlike the examples, confirm the installed Manim package:

```bash
python - <<'PY'
import manim
print(getattr(manim, "__version__", "unknown"))
print(manim.__file__)
PY
```

If the package is the old 3Blue1Brown Manim, replace it with Manim Community in the user's environment.

### ManimML has undeclared runtime dependencies

The package metadata does not declare all dependencies used by optional workflows. Install the relevant public dependencies for the requested workflow:

- Neural-network scenes: `manim`, `numpy`, `pillow`.
- Decision-tree scenes: add `scikit-learn`, `matplotlib`, `pillow`.
- MCMC/probability scenes: add `scipy`, `matplotlib`, `seaborn`, `tqdm`.
- Test-style checks: add `pytest`.

## Render-stack failures

### Cairo/Pango/ManimPango/ffmpeg errors

Symptoms may mention `pangocairo`, `ManimPango`, `pycairo`, `ffmpeg`, or missing shared libraries. These are Manim Community environment problems rather than ManimML API mistakes.

Recovery sequence:

1. Run import-only checks first:

   ```bash
   python scripts/check_manimml_environment.py
   ```

2. Run Manim's version command:

   ```bash
   manim --version
   ```

3. Render a minimal Manim scene that does not use ManimML. If that fails, repair the Manim installation before debugging ManimML code.
4. Prefer a Conda or system-package route that supplies Cairo/Pango/ffmpeg cleanly; avoid mixing incompatible binary packages in one environment.

### LaTeX or font failures

Some Manim text/code objects require LaTeX or fonts. ManimML's basic layer diagrams should construct without custom fonts, but examples using `Code`, `MathTex`, or fancy text can fail.

Recovery:

- Remove or simplify the text/code object for a smoke test.
- Render a still frame with `manim -ql -s` before a full animation.
- Install LaTeX only when the user actually needs LaTeX-rendered text.

### Headless machine / display problems

Most ManimML workflows can use CPU rendering. OpenGL shader examples are optional and may need a working GL context. For headless statistical plots, set Agg before creating matplotlib figures:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

Do not claim OpenGL coverage unless the user's environment can create an OpenGL context and the task explicitly needs it.

## Object construction versus rendering

Separate failures into three stages:

1. **Import failure**: `import manim`, `import manim_ml`, or public class import fails.
2. **Construction failure**: Python builds a `NeuralNetwork`, `DecisionTreeDiagram`, `MCMCAxes`, or helper object but raises an API/data error.
3. **Render failure**: objects construct, but `manim` fails while producing media.

Use the root check script for stage 1 and broad stage 2 checks, then sub-skill helper scripts for workflow-specific stage 2 checks. Only diagnose stage 3 after stages 1 and 2 pass.

## Performance and safety

- Avoid high-quality render flags (`-pqh`) until the scene layout is validated.
- Use tiny generated arrays/images for smoke tests.
- Keep MCMC smoke tests around 10-25 iterations; increase only after construction succeeds.
- Do not run long training/model-generation scripts to create visual assets unless the user explicitly asks for that separate ML task.
- Generated helper scripts in this skill do not download data, need credentials, or render by default.

## Known source quirks shared across workflows

- ManimML currently prints some construction information to stdout.
- Some source files use string identity comparisons and can emit Python `SyntaxWarning` messages; these warnings did not block import/object-construction checks.
- Several custom animation paths are less mature than static object construction. Prefer `self.add(...)` or short/still renders for first checks, then add custom animations.
- Full graphical regression tests are heavier than the package/API smoke checks and should be saved for final verification or repository development.
