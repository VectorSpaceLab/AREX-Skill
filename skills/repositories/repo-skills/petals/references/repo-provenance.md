# Petals Repo Provenance

Schema: `disco.repo-provenance.v1`

This generated repo skill was distilled from a Petals checkout and is intended for versioned package operation across projects.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | `bigscience-workshop/petals` |
| Public remote URL | `https://github.com/bigscience-workshop/petals.git` |
| Commit | `22afba627a7eb4fcfe9418c49472c6a51334b8ac` |
| Commit subject | `Upgrade Pydantic to >= 2.0.0 (#607)` |
| Branch | `main` |
| Package distribution | `petals` |
| Package version from source/import inspection | `2.3.0.dev2` |
| Python support from package metadata | `>=3.8` |

## Evidence paths

The skill was built from these repository-relative evidence paths: `README.md`, `pyproject.toml`, `setup.cfg`, `Dockerfile`, CI workflows, `src/petals/`, prompt-tuning notebooks, benchmarks, and tests.

## Refresh triggers

Refresh this skill when Petals changes its package version, supported Transformers/Hivemind/Torch range, public client constructors, `RemoteSequential`, `InferenceSession`, `PTuneConfig`, PEFT utilities, server CLI flags, model-family support, DHT prefix rules, benchmark arguments, or public guidance around model access/privacy/security/hardware.

## Known distillation limits

Full public-swarm inference, private-swarm native tests, notebook training, benchmark execution, and production GPU serving were treated as optional/networked or long-running checks rather than assumed local facts. Local environment preparation verified imports, API signatures, CLI parser help, and torch CUDA visibility. Optional bitsandbytes/PEFT execution was not verified because the inspected optional backend stack was incompatible with the pinned bitsandbytes release.
