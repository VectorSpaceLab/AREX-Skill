# Dense-to-MoE Workflow

`mergekit-moe` converts dense model checkpoints into a sparse mixture of
experts. It keeps attention and normalization from `base_model`, takes MLP
weights from each `experts[].source_model`, creates router weights, and writes a
new MoE checkpoint plus tokenizer when copying is enabled.

## Inputs and command

The exact command is:

```bash
mergekit-moe CONFIG_PATH OUT_PATH [special options] [common options]
```

The YAML contract is:

```yaml
base_model: ./self-attention-donor
architecture: qwen       # optional output-family selector
gate_mode: hidden        # hidden, cheap_embed, random, or uniform_random
dtype: bfloat16          # float32, float16, bfloat16, or omit for base dtype
experts_per_token: 2     # optional; must be >= 1 and <= number of experts
experts:
  - source_model: ./expert-a
    positive_prompts:
      - "prompt representative of expert A"
    negative_prompts: []
    noise_scale: 0.0
    residual_scale: 1.0
  - source_model: ./expert-b
    positive_prompts:
      - "prompt representative of expert B"
shared_experts:           # optional; architecture-dependent
  - source_model: ./shared
    positive_prompts: ["prompt"]
    residual_scale: 0.1
```

`positive_prompts`, `negative_prompts`, `noise_scale`, and `residual_scale` are
per-expert optional fields. For non-random gate modes every routed expert must
have at least one positive prompt, and prompts must distinguish experts. The
config validator rejects fewer experts than `experts_per_token`, and rejects
identical source models unless the explicit training-caveat flag is supplied.
`random` and `uniform_random` do not need prompts; the CLI help exposes the
training-caveat flag, not a separate gate-mode option.

Special CLI options are:

```text
--load-in-4bit
--load-in-8bit
--i-understand-this-is-not-useful-without-training
```

Use 4-bit or 8-bit loading only to reduce the memory used to compute hidden
states; it is not a general output quantization setting. `--device`,
`--cuda`, `--trust-remote-code`, serialization, and other common options are
also accepted.

## Gate modes

- `hidden` is the default-quality choice. It evaluates each prompt through the
  base model and gives layer-specific router vectors. It needs the tokenizer,
  model execution, and memory for the base model (reduced by 4/8-bit loading
  when compatible extras are installed).
- `cheap_embed` uses prompt token embeddings and reuses gate parameters across
  layers. It is cheaper and generally less effective.
- `random` initializes gates randomly and is appropriate when the result will
  be trained, especially sparse upcycling. It is not evidence of a useful
  finished MoE.
- `uniform_random` matches a uniform random linear-style initialization in the
  installed config model. It is source-supported but less prominently
  documented; verify the installed version before relying on it.

The build warns about degenerate router gates. Treat that warning as a stop for
an inference-ready result: inspect prompt separation, tokenizer behavior, and
expert diversity rather than blindly saving the model.

## Supported output families

Architecture selection is inferred from the input model configs unless
`architecture:` narrows it. The inspected implementations support:

- **Mixtral**: all base and routed expert configs must share one model type,
  and that type must be `llama` or `mistral`; shared experts are rejected.
- **DeepSeek MoE**: same-family `llama`/`mistral` inputs; at most one shared
  expert, and a shared expert cannot have positive or negative gating prompts.
- **Qwen MoE (Qwen2 MoE output)**: requires exactly one shared expert, requires
  shared-expert prompts except in random gate mode, and accepts uniform input
  model type `qwen2`, `llama`, or `mistral` as supported by the installed
  Transformers config.
- **Qwen3 MoE**: requires uniform `qwen3` input models and rejects shared
  experts.

Qwen output classes are optional imports: an older/incomplete Transformers
installation can remove them from the candidate set. The exact installed
candidate list is an environment fact, not a promise to use every family.
Use verbose logging (`-v`) to inspect rejection explanations. An explicit
architecture that has no compatible candidate stops before writing output.

All inputs must be architecturally and dimensionally compatible with the
selected writer. `--allow-crimes` does not make an unsupported family valid.
For model resolution, remote-code trust, checkpoint keys, memory, and backend
issues, hand off to [model-io-and-architecture](../../model-io-and-architecture/SKILL.md).

## Outputs, training caveat, and safe stops

The output is an architecture-specific model directory with generated config,
expert/router tensors, and (by default) a copied tokenizer. With model-card
writing enabled, the source config is recorded as `mergekit_moe_config.yml`.
The writer may warn that a non-power-of-two expert count is not usable by
llama.cpp; treat that as a deployment constraint, not a cosmetic warning.

Stop before running when:

- the base, every expert, or tokenizer is missing or would require an
  unapproved network/credential;
- required Transformers, PEFT/quantization extras, or remote-code support are
  unavailable;
- model types differ, the requested architecture is unsupported, shared-expert
  constraints fail, or tensor dimensions do not match;
- gates would be degenerate, prompts are identical/nonrepresentative, or all
  experts are the same without an explicit plan to train;
- the output path collides with an input or an existing model that has not been
  explicitly approved for replacement.

For sparse upcycling or any all-identical-expert construction, retain the
training caveat in the handoff. A writer success is not an inference-quality
claim.
