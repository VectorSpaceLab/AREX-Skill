# DreamerV3 JAX Model Troubleshooting

Use this table when model construction, policy inference, training loss, checkpoint restore, or JAX sharding fails. It intentionally focuses on model/JAX internals; route installation/Docker/system repair to `results-ops` and environment/replay contracts to `embodied-dataflow`.

## Fast Triage

1. **Parse config without constructing the Agent**:

   ```bash
   python scripts/inspect_model_config.py defaults debug size1m
   python scripts/inspect_model_config.py --config-file path/to/config.yaml
   ```

2. **If the failure is numeric or shape-related**, reproduce with CPU/debug/small dimensions in a fresh process.
3. **If the failure is data-space-related**, confirm exact observation/action keys and dtypes before changing model code.
4. **If the failure follows a size or module-name change**, suspect checkpoint/PyTree incompatibility first.

## Symptom Matrix

| Symptom | Likely cause | Action |
|---|---|---|
| `No GPU/TPU found`, CUDA platform unavailable, or backend import fails before model code | Backend/runtime mismatch, not a model-contract issue. | Use CPU debug to keep working on model logic; route installation/driver repair to `results-ops`. |
| CUDA OOM or allocator failure at startup | Preallocation or model too large. | Set `jax.prealloc=False`, shrink `batch_size`, `batch_length`, `imag_length`, or use `debug`/`size1m`. Relaunch fresh process. |
| Wrapper prints `ALERT: Wrong number of devices` and waits | `jax.expect_devices` positive and actual device count differs. | Fix device visibility, `expect_devices`, `mock_devices`, or selected platform. Do not wait for it to recover. |
| Device index out of range | `policy_devices` or `train_devices` refers to unavailable index. | Inspect device count under the selected platform; adjust devices or `mock_devices`. |
| Mesh shape assertion | Product of `policy_mesh`/`train_mesh` after resolving `-1` does not equal selected device count. | Use a mesh string whose product matches devices, usually `-1,1,1` for data-only sharding. |
| `Inter-node TP is not supported!` | Tensor-parallel mesh axis `t` exceeds selected local devices. | Avoid inter-node tensor parallelism; keep `t` within local selected devices. |
| `jax_transfer_guard` error | Host/device transfer attempted inside JIT when transfer guard is disallowing it. | Avoid `np.asarray`, printing arrays, or Python-side conversions inside transformed code; collect outputs through wrapper-returned metrics. |
| `jax_disable_jit`/debug run is extremely slow | CPU/debug route is active. | Keep debug dimensions tiny (`debug`/`size1m`) and use it only to localize the issue. |
| Non-finite policy output assertion | Encoder, RSSM, policy head, or input data produced NaN/Inf. | Read `debugging-numerics.md`; inspect finite diagnostics by component and run CPU/debug with `float32` compute dtype if needed. |
| Floating observation assertion fails | Observation contains NaN/Inf before model. | Route data source to `embodied-dataflow`; do not mask model assertions. |
| Observation keys assertion fails | `obs` keys differ from `obs_space`. | Fix environment wrapper/data assembly; lifecycle keys are expected in `obs_space`, but encoder/decoder exclude them internally. |
| Action key or action shape mismatch | `act_space` changed or policy head output map mismatches actions. | Confirm discrete vs continuous spaces and `policy_dist_disc`/`policy_dist_cont`. Do not reuse incompatible checkpoints. |
| Image encoder assertion on dtype | Image observation is not `uint8`. | Provide raw `uint8` image observations; encoder handles scaling. Do not pre-normalize images to floats for this path. |
| Image encoder/decoder spatial assertion | Downsampled min resolution outside 3..16. | Adjust input image size, `depths`/`mults`, `outer`, or `strided`; inspect config first. |
| `deter % blocks` assertion | RSSM deterministic size incompatible with grouped transition. | Set `agent.dyn.rssm.deter` divisible by `agent.dyn.rssm.blocks`. |
| Decoder `deter % bspace` assertion | Decoder block-space projection incompatible. | Set `agent.dec.simple.bspace` to a divisor of `agent.dyn.rssm.deter`, or disable/change bspace knowingly. |
| Loss key set assertion | Added/removed loss or observation reconstruction without matching `loss_scales`. | Update `agent.loss_scales`; remember `rec` expands to decoder observation keys. |
| Loss shape assertion `(B,T)` fails | New head/loss did not aggregate event dims or preserve batch/time dims. | Wrap output with `outs.Agg` when needed and reduce only event dims, not batch/time dims. |
| Optimizer asserts scalar `float32` loss | Loss returned non-scalar or non-float32 dtype. | Cast/aggregate final loss to scalar `jnp.float32`; keep activation compute dtype separate from loss dtype. |
| `grad_norm` is NaN but losses are finite | Backward pass/dtype/optimizer instability. | Try `jax.compute_dtype=float32`, inspect custom gradients, and check float16 grad scaling metrics if applicable. |
| `No matching rule found for param key` | Custom parameter partition rules miss a Ninjax key. | Add a fallback rule such as `('.*', P())` or cover every parameter key. |
| `No matching rule found for activation key` | Activation partition rules miss a `nets.LAYER_CALLBACK` name. | Add activation rule coverage or disable custom activation partitioning for the component. |
| `SlowModel` says `no parameters to track` | Target slow model used before source module has parameters. | Ensure source value head is initialized by a call before `SlowModel` accesses or updates. |
| Full checkpoint restore shape mismatch | Model size, spaces, head bins, or module names changed. | Use a new checkpoint/logdir, restore matching architecture, or regex-load a compatible subset. |
| Regex checkpoint load silently leaves new params random | Regex intentionally loaded only matching keys. | Treat as partial initialization; run finite policy and short train smoke before long runs. |
| LayerScan inner shape mismatch | Scanned inputs or state missing leading `count` dimension. | Reduce to a tiny case and inspect Ninjax context after init/apply; read `debugging-numerics.md#layerscan-pitfalls`. |

## Config Fix Patterns

### Small CPU model for laptop/debug smoke

Use `debug` for CPU/debug flags and extremely small network dimensions. Add `size1m` if you want a small named size preset, but remember that later patches can override earlier ones.

```bash
python scripts/inspect_model_config.py defaults debug size1m
```

Check warnings for:

- CUDA platform combined with debug/prealloc choices.
- `deter` not divisible by `blocks` or `bspace`.
- size/debug patches that imply checkpoint incompatibility.

### Safer numeric debug

Prefer a fresh process with:

```text
jax.platform=cpu
jax.prealloc=False
jax.debug=True
jax.jit=False              # optional, narrow repro only
jax.compute_dtype=float32  # optional, numeric clarity
```

If `jax.debug_nans=True` is used, expect major slowdown and possible changes in transfer behavior.

### Checkpoint subset load after architecture edits

If an old checkpoint must be reused, load only stable keys:

```text
^(enc|dyn)/
^(enc|dyn|pol)/
^pol/
```

Do not use regex loading to hide incompatible semantics. After any partial restore, run a finite policy smoke and inspect losses/entropies before long training.

## Model Extension Guardrails

- Keep Ninjax path names stable (`self.sub('name', ...)`) when checkpoint compatibility matters.
- Preserve RSSM feature keys: `deter`, `stoch`, and `logit`.
- Preserve batch/time leading dimensions through heads and losses.
- Return output objects that implement `.pred()`, `.loss()`, `.sample()`, `.logp()`, `.entropy()`, and `.kl()` when using them interchangeably with existing heads.
- Add metrics for new losses and scale them in `loss_scales`.
- Verify policy finite diagnostics after any extension that touches encoder, RSSM, or policy head.
