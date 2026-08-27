---
name: manim-ml
description: "Use ManimML to build Manim Community animations and visual
  explanations for machine-learning concepts, especially neural-network
  diagrams, decision trees, MCMC, probability, and plotting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: manim_ml
license: MIT
---

# ManimML Repo Skill

## When to use this skill

Use this skill when the task asks for Python code, Manim scenes, debugging help, or workflow guidance involving ManimML / `manim_ml`:

- Neural-network architecture diagrams, CNNs, max pooling, image inputs, embeddings, triplet/paired-query visuals, vector/math nodes, forward-pass animations, dropout, residual/skip connections, or VAE-style diagrams.
- Statistical/probability animations such as scikit-learn decision-tree diagrams, decision surfaces, Metropolis-Hastings / MCMC chains, Gaussian mobjects, and matplotlib figures converted to Manim images.
- Package-specific install/import checks, Manim Community compatibility checks, or troubleshooting for ManimML scene construction.

Do **not** use this skill for unrelated Manim projects that do not use ManimML APIs, for training real ML models, or for maintaining this source repository unless the user specifically asks for repo development rather than package use.

## Environment expectations

ManimML is a Manim Community extension. A usable environment should have:

```bash
pip install manim_ml
python - <<'PY'
import manim
import manim_ml
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer
print(getattr(manim, "__version__", "unknown"))
print(NeuralNetwork, FeedForwardLayer)
PY
```

For decision-tree and MCMC workflows, the active environment also needs common scientific packages such as NumPy, Pillow, SciPy, matplotlib/seaborn, scikit-learn, and tqdm. Full rendering may require the usual Manim Community render stack (for example Cairo/Pango/ffmpeg and, for some text workflows, LaTeX).

Run the bundled shared smoke helper before deeper debugging:

```bash
python scripts/check_manimml_environment.py --json
```

## Route map

| User task | Read next |
| --- | --- |
| Build a feed-forward, CNN, image-CNN, embedding, triplet, paired-query, vector/math, dropout, residual, VAE-style, or forward-pass ManimML scene | [neural-network-visualization](sub-skills/neural-network-visualization/SKILL.md) |
| Generate a small standalone Manim scene without repo assets | [neural-network helper script](sub-skills/neural-network-visualization/scripts/render_neural_network_example.py) through the neural-network sub-skill |
| Build or debug scikit-learn decision-tree, decision-surface, MCMC, Gaussian/probability, or matplotlib-to-image workflows | [statistical-visualizations](sub-skills/statistical-visualizations/SKILL.md) |
| Verify package imports, Manim Community compatibility, or cross-cutting render issues | [root troubleshooting](references/troubleshooting.md) and [check script](scripts/check_manimml_environment.py) |
| Decide whether this generated skill is stale for a checkout | [repo provenance](references/repo-provenance.md) |

## Cross-cutting references and scripts

- [Repo provenance](references/repo-provenance.md): source commit, package version, dirty state, and evidence paths used to build this skill.
- [Root troubleshooting](references/troubleshooting.md): install/import, Manim Community, render-stack, optional dependency, headless plotting, and performance guidance shared by all workflows.
- [Router metadata](references/repo-routing-metadata.json): structured scenario placement for managed repo-skill import.
- [Environment check script](scripts/check_manimml_environment.py): safe import/object-construction/sampler checks with optional JSON output.

## Operating principles

1. Prefer ManimML public APIs and bundled examples from this skill over copying source-repository example paths.
2. Keep first renders small: use `manim -ql -s` for a still frame before long video renders.
3. Generate tiny local fixtures for image/triplet/decision-tree examples unless the user explicitly supplies image paths.
4. Treat rendering as a separate step from object construction. First prove imports and object construction, then render.
5. Keep headless statistical workflows on matplotlib's Agg backend before creating figures.
6. Mention current source limitations honestly: some animation helpers are incomplete or noisy, and full graphical tests are heavier than API smoke checks.

## Quick examples

Generate an asset-free neural-network scene file:

```bash
python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py \
  --mode image-cnn \
  --scene-file image_cnn_scene.py
```

Run compact statistical construction checks without rendering:

```bash
python sub-skills/statistical-visualizations/scripts/build_statistical_visualizations.py \
  --example all \
  --iterations 8 \
  --json
```

Then render only after the generated code or construction check succeeds.
