---
name: model-internals
description: "Explain MUNIT trainer, generator, discriminator, and porting
  internals for safe architecture modification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MUNIT model internals

Use this sub-skill when a Researcher is modifying, debugging, or porting the MUNIT/UNIT model code: trainer class contracts, AdaIN generator wiring, UNIT VAE generator behavior, multi-scale discriminator losses, normalization/activation/padding options, checkpoint compatibility, and legacy PyTorch migration issues.

This sub-skill is self-contained operating knowledge distilled from the repository trainer, network, utility, config, tutorial, and CLI evidence. It intentionally avoids depending on the original source checkout for runtime guidance.

## Boundaries

Use this sub-skill for:

- Understanding `MUNIT_Trainer(hyperparameters)` and `UNIT_Trainer(hyperparameters)` object graphs, update methods, losses, save/resume state, and CUDA assumptions.
- Editing or reimplementing `AdaINGen(input_dim, params)`, `VAEGen(input_dim, params)`, `MsImageDis(input_dim, params)`, encoders, decoder, blocks, AdaIN, LayerNorm, or related helpers.
- Checking whether a config is architecture-compatible before changing `gen`, `dis`, `input_dim_*`, loss, or style-code settings.
- Planning a modern PyTorch port without accidentally changing style-code semantics, GAN loss semantics, InstanceNorm checkpoint loading, or VGG side effects.

Reroute instead:

- End-user training commands, resume commands, run outputs, and long GPU jobs: `../training/`.
- Single-image inference, example-guided translation, batch inference, and metrics: `../inference-and-evaluation/`.
- Runtime installation, legacy CUDA/PyTorch setup, dependency probes, and Docker/conda decisions: `../environment-and-setup/`.
- Dataset folder/list layouts and YAML path repair: `../data-and-configuration/`.

## Start here

1. Read `references/architecture.md` for the model graph and dataflow before editing code.
2. Read `references/api-reference.md` for class signatures, expected config keys, method behavior, and return shapes.
3. For ports or extensions, read `references/porting-and-extension.md` before touching deprecated PyTorch APIs or checkpoint loading.
4. For failure diagnosis, use `references/troubleshooting.md` to map symptoms to causes and safe fixes.
5. Run the static helper against a target checkout or config when available. It does not import MUNIT modules, allocate CUDA tensors, download weights, or instantiate trainers:

   ```bash
   python scripts/inspect_munit_architecture.py --help
   python scripts/inspect_munit_architecture.py \
     --repo-root /path/to/user/munit-checkout \
     --config configs/demo_edges2handbags_folder.yaml \
     --trainer MUNIT
   ```

## Critical operating facts

- MUNIT is two-domain: domain A and domain B each get a generator and discriminator. Checkpoints store generator/discriminator state as dictionaries with `a` and `b` entries.
- `MUNIT_Trainer` uses AdaIN generators and a sampled style code with shape `[batch, gen.style_dim, 1, 1]`; `UNIT_Trainer` uses VAE-style content generators and needs UNIT KL loss weights not present in the MUNIT demo configs.
- AdaIN decoder calls require dynamic AdaIN weight/bias assignment before every decode. Calling the decoder path before assigning these parameters triggers an assertion.
- The original trainer and inference paths call `.cuda()` directly. Treat CPU-only inspection as static verification, not proof that unmodified training or inference will run.
- When `vgg_w > 0`, the legacy utility may try to create a model directory, download a VGG `.t7` file, convert it with `load_lua`, and save converted weights. Keep that side effect out of static checks.

## Reference map

- `references/api-reference.md` - verified class signatures, trainer methods, network constructors, config keys, and selected utility helpers.
- `references/architecture.md` - MUNIT/UNIT model graph, AdaIN parameter flow, discriminator scales, and loss/update sequence.
- `references/porting-and-extension.md` - safe extension and modernization guidance for style dimensions, devices, PyTorch APIs, YAML, VGG, and state dicts.
- `references/troubleshooting.md` - symptom-driven fixes for AdaIN, checkpoints, unsupported options, GAN loss choices, legacy APIs, InstanceNorm conversion, CUDA assumptions, and VGG download side effects.
- `scripts/inspect_munit_architecture.py` - self-contained static inspector for source text and config files.
