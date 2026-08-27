# Repository Provenance

Read this before deciding whether the operating skill still matches a
checkout. If the commit, source evidence, package requirements, or public
entry-point behavior differs, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:13:00Z",
  "repository": {
    "name": "rPPG-Toolbox",
    "remote_url": "https://github.com/ubicomplab/rPPG-Toolbox.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b7500b848f84ad7f86e277b4612563b69f4f88f9",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/rppg-toolbox",
      "skills/tests/rppg-toolbox"
    ]
  },
  "packages": [
    {
      "name": "rPPG-Toolbox",
      "version": null,
      "import_names": [
        "config",
        "dataset",
        "evaluation",
        "neural_methods",
        "unsupervised_methods"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "main.py",
      "config.py",
      "dataset",
      "neural_methods",
      "unsupervised_methods",
      "evaluation"
    ],
    "docs": [
      "README.md",
      "requirements.txt",
      "setup.sh"
    ],
    "examples": [
      "configs/infer_configs",
      "configs/train_configs",
      "tools/motion_analysis",
      "tools/preprocessing_viz",
      "tools/output_signal_viz",
      "tools/mamba/test_mamba_module.py"
    ],
    "tests": [
      "neural_methods/model/FactorizePhys/test_FactorizePhys.py",
      "neural_methods/model/FactorizePhys/test_FactorizePhysBig.py",
      "tools/mamba/test_mamba_module.py"
    ],
    "configs": [
      "configs",
      "dataset/BP4D_BigSmall_Subject_Splits"
    ]
  }
}
```

The tracked source was clean at the start of construction. The dirty paths
above are the generated runtime skill and private review artifacts created by
this run; they are not source changes to the package. Large checkpoints,
preprocessed data, generated model outputs, vendored Mamba code, and notebooks
are intentionally not part of this public operating graph.

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as
  potentially stale.
- If tracked source files, requirements, public config keys, loader dispatch,
  model dispatch, or evaluator behavior changed, refresh the skill even if the
  commit is unchanged in a copied checkout.
- If a future checkout is dirty in source paths rather than only generated
  skill/review paths, preserve those changes as an explicit evidence decision
  before refreshing.
