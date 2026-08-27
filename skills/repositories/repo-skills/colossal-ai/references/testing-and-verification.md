# Testing and Verification Notes

This skill separates safe checks from expensive native examples.

## Safe package checks

```bash
python scripts/check_colossalai_environment.py --check-cli
colossalai --help
colossalai run --help
colossalai check -i
```

These checks should not download models, start services, or run training.

## Focused native candidates

Prefer a small subset when verifying a local environment or generated guidance:

- CLI: `colossalai --help`, `colossalai run --help`, `colossalai check -i`.
- Pure config: a minimal `Config` load or equivalent config object construction.
- Booster/device: a tiny `Accelerator` or one-process `torchrun` plugin construction smoke.
- Inference config: construct `InferenceConfig` and simple request/sequence structures; do not load real LLMs by default.
- ShardFormer utility: small CUDA utility tests are acceptable if a GPU is available and known to be short.

## Expensive or conditional examples

Do not run these without explicit assets and approval: LLaMA/GPT/Mixtral/Grok/Stable Diffusion benchmarks, 4+ or 8+ GPU examples, application package tests, service/client benchmarks, and AOT CUDA extension builds.
