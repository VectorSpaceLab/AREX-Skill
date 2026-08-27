# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Keras-GAN. If the current repo commit, dirty state, dependency metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:46:04Z",
  "repository": {
    "name": "Keras-GAN",
    "remote_url": "https://github.com/eriklindernoren/Keras-GAN.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3ff3be4b4b2fa338b18e469888b6f0b7a1b2db48",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "Keras-GAN",
      "version": null,
      "import_names": []
    },
    {
      "name": "tensorflow",
      "version": "1.15.5",
      "import_names": [
        "tensorflow"
      ]
    },
    {
      "name": "Keras",
      "version": "2.2.4",
      "import_names": [
        "keras"
      ]
    },
    {
      "name": "keras-contrib",
      "version": "2.0.8",
      "import_names": [
        "keras_contrib"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "aae",
      "acgan",
      "bgan",
      "bigan",
      "ccgan",
      "cgan",
      "cogan",
      "context_encoder",
      "cyclegan",
      "dcgan",
      "discogan",
      "dualgan",
      "gan",
      "infogan",
      "lsgan",
      "pix2pix",
      "pixelda",
      "sgan",
      "srgan",
      "wgan",
      "wgan_gp"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "README.md example commands",
      "standalone model scripts"
    ],
    "tests": [
      "pixelda/test.py"
    ],
    "configs": [
      "requirements.txt"
    ],
    "excluded": [
      "assets",
      "*/images",
      "*/saved_model",
      "skills/tests",
      "skills/disco",
      ".git"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If the Keras-GAN scripts are ported to modern Keras/TensorFlow, or if `requirements.txt` changes materially, refresh this skill before relying on compatibility guidance.

## Evidence Notes

- The source checkout was already dirty because generated `skills/` artifacts existed during construction.
- Full training loops and network download scripts were not executed; they remain classified as expensive or network side-effect candidates.
