# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ManimML. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:25:39Z",
  "repository": {
    "name": "ManimML",
    "remote_url": "https://github.com/helblazer811/ManimML.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5e8f7cb69f23919f9ec7e880fb22c1ca2f841c08",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "manim_ml",
      "version": "0.0.17",
      "import_names": ["manim_ml"]
    }
  ],
  "evidence": {
    "source_roots": [
      "manim_ml/",
      "manim_ml/neural_network/",
      "manim_ml/decision_tree/",
      "manim_ml/diffusion/",
      "manim_ml/utils/"
    ],
    "docs": [
      "Readme.md",
      "docs/source/"
    ],
    "examples": [
      "examples/readme_example/",
      "examples/basic_neural_network/",
      "examples/cnn/",
      "examples/lenet/",
      "examples/gan/",
      "examples/interpolation/",
      "examples/variational_autoencoder/variational_autoencoder.py",
      "examples/decision_tree/",
      "examples/mcmc/"
    ],
    "tests": [
      "tests/test_layers.py",
      "tests/test_feed_forward.py",
      "tests/test_neural_network.py",
      "tests/test_conv_padding.py",
      "tests/test_convolutional_2d_layer.py",
      "tests/test_embedding_layer.py",
      "tests/test_paired_query.py",
      "tests/test_triplet.py",
      "tests/test_variational_autoencoder.py",
      "tests/test_nn_dropout.py",
      "tests/test_color_scheme.py",
      "tests/test_decision_tree.py",
      "tests/test_mcmc.py",
      "tests/test_plotting.py",
      "tests/test_show_gaussian.py"
    ],
    "configs": [
      "setup.py"
    ],
    "excluded_evidence_classes": [
      "docs/build/ generated docs output",
      "examples/media/ rendered output",
      "examples/variational_autoencoder/autoencoder_models/ heavyweight model-training artifacts",
      "standalone exploratory examples not clearly exported as public ManimML APIs",
      "skills/tests/ review artifacts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from the snapshot, check whether package source, docs, examples, or tests changed. The dirty `skills/` path here reflects generated skill/artifact output during creation.
- If `setup.py`, public imports, layer signatures, or optional dependency behavior changed, run `refresh-repo-skill` even if the commit is unchanged.
- If Manim Community introduces breaking API changes relative to the verified 0.18.x inspection behavior, rerun verification and refresh references/scripts as needed.
