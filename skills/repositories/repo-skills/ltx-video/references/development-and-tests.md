# Development and test selection

This reference is for maintaining the skill or repository. It separates safe structural checks from tests that can download models or require specialized hardware.

## Safe skill-bundle checks

Run from `skills/disco/ltx-video/`:

```bash
python scripts/check_ltx_video_env.py --help
python scripts/check_ltx_video_env.py --json
python -m py_compile scripts/check_ltx_video_env.py
python -m json.tool references/repo-routing-metadata.json
```

Also verify that every Markdown link in the root and leaf `SKILL.md` files resolves inside the bundle, each declared script/reference exists, and exactly these operating leaves remain routable:

- `sub-skills/local-inference/SKILL.md`
- `sub-skills/model-configs/SKILL.md`
- `sub-skills/pipeline-components/SKILL.md`

The leaf helpers are designed for safe preflight. Their `--help` paths should not import the LTX-Video package, download models, or start generation:

```bash
python sub-skills/local-inference/scripts/build_inference_command.py --help
python sub-skills/model-configs/scripts/inspect_ltxv_config.py --help
python sub-skills/pipeline-components/scripts/check_components.py --help
```

## Safe repository-native candidates

With the repository's test dependencies installed, the source snapshot identified these focused candidates:

```bash
python inference.py --help
pytest tests/test_scheduler.py -q
pytest tests/test_vae.py::test_downscale_factors -q
```

`python inference.py --help` may require the inference dependency group because parser definitions live with inference imports. Scheduler and VAE tests exercise code contracts but do not verify a full checkpoint generation run.

The synthetic VAE shape/causality cases may be reasonable on CPU but cost more memory/time:

```bash
pytest tests/test_vae.py::test_encode_decode_shape tests/test_vae.py::test_temporal_causality -q
```

Run them only when that additional cost is acceptable.

## Not routine verification gates

Do not run the following by default:

- `tests/test_inference.py` full generation cases;
- `tests/test_configs.py` across model configurations;
- prompt-enhancement tests;
- checkpoint quality or performance benchmarks;
- FP8/Q8 runtime tests.

Those paths can require Hugging Face downloads/cache, large checkpoints, GPU/MPS capacity, media codecs, prompt-enhancer assets, a spatial upscaler, or external FP8 kernels. Run them only with explicit authorization and record backend, model/cache, network, and skip conditions.

## Interpretation rules

- Environment checker success means the requested imports/backend requirements passed; it does not verify inference.
- Config inspector success means static configuration checks passed; it does not verify that remote assets exist or fit memory.
- Component checks mean the selected component contract behaved as expected; they do not prove end-to-end quality.
- Record skips honestly. Never convert a missing optional backend into a claimed pass.

## Source maintenance signals

Refresh the skill if any of these change: `pyproject.toml` dependencies/extras; `InferenceConfig` or CLI fields; pipeline/scheduler/VAE/transformer signatures; config filenames or schema; model table; prompt-enhancement behavior; checkpoint/upscaler locations; or repository test layout. Preserve ownership boundaries and keep heavyweight execution out of bundled helpers.
