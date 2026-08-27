# Extension and evolution troubleshooting

Use this table to stop at the smallest safe boundary. Core method extension and
CPU task graphs do not require the evolutionary extras.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Decorator raises `Merge methods must have a 'tensors' parameter` | Function has no parameter literally named `tensors`. | Add `tensors` and use the exact `List[torch.Tensor]` runtime annotation. Avoid postponed annotations in decorator modules. |
| Decorator rejects the tensors annotation | It is `Sequence`, `list[Tensor]` under an unsupported runtime form, a string, or has the wrong element type. | Match the 0.1.4 contract exactly, then run the bundled AST preflight and a registration import in a clean test process. |
| Decorator rejects `base_tensor` | The annotation is neither `torch.Tensor` nor `Optional[torch.Tensor]`. | Use a required tensor annotation when YAML must provide `base_model`; use Optional when no base model is valid. Test both branches. |
| Method imports but fails with a missing argument | A function parameter has no supported scalar/vector annotation or is not one of the special context names. | Limit parameters to `bool`/`int`/`float`, `List[int]`/`List[float]`, `base_tensor`, `base_model`, and `output_weight`; give required values to the YAML owner. |
| Output has the wrong shape, dtype, or device | The decorator does not validate semantic tensor output; the class task may return an arbitrary value. | Add a tiny CPU fixture asserting one tensor, shape, dtype, and expected values. Let the executor move declared dependency tensors rather than hard-coding a device. |
| Per-model weights pair with the wrong tensor | The callable sees lists of tensors/values, not model-reference keys; order assumptions were not tested. | Use a two-model fixture with distinct sentinel values and assert correspondence. Keep model ordering stable in the method's supported configuration path. |
| Base model appears twice or is missing | `base_tensor` was omitted/present contrary to the intended API, or YAML base-model membership was misunderstood. | With `base_tensor`, the base is separate and required/optional by annotation. Without it, a configured base is first in `tensors`. Test the exact intended YAML shape through the normal config route. |
| `ConfigParameterDef` validation fails unexpectedly | A type was passed as the second positional argument from an outdated example. | In 0.1.4 use `ConfigParameterDef(name, required=False, default_value=None)`; parameter type behavior is handled by the consuming configuration/task contract. |
| YAML says a custom method is unknown | Defining module was never imported, registration name differs from `merge_method`, or a class was not added to the static list. | Use the AST checker, add a guaranteed import for decorator methods, or import and instantiate the class in `STATIC_MERGE_METHODS`. Inspect `REGISTERED_MERGE_METHODS` in a clean process. |
| A custom name replaces an existing method | Decorator registration writes directly to the registry mapping and does not provide a collision guard. | Choose a unique name, assert the final registry entry belongs to the intended implementation, and document the public name. |
| `Executor` reports `networkx.NetworkXUnfeasible` | `arguments()` created a dependency cycle, including a self-edge. | Draw the dependency closure, remove the cycle, and add a regression test expecting the exception. Never execute a partially ordered graph. |
| Task dependency value is absent or `execute()` raises a keyword error | A key from `arguments()` does not match an `execute()` parameter. | Treat the argument dictionary as the task's call signature; make names identical and test a graph with one dependent and one independent node. |
| A task executes on an unexpected device | `uses_accelerator()` is false/true incorrectly, or the task relies on tensor state outside declared dependencies. | Check `math_device` and `storage_device`, declare accelerator use only for tensor-heavy work, and test nested tensor movement. General CUDA/multi-GPU placement belongs to the architecture route. |
| A graph is unexpectedly slow or memory-heavy | Large dependency closure, poor grouping/priority, repeated tensor transfer, or missing cache. | Inspect `group_label()` and `priority()`, use `cached_values` only for verified reusable results, and test a tiny graph before considering GPU changes. |
| `mergekit-evolve --help` fails with `ModuleNotFoundError: cma` | The optional evolution stack is absent; imports occur before Click parses help. | Install the approved `evolve` extra in an isolated environment, or record evolution as blocked/optional. This does not block core mergekit method work. Check `ray`, `lm_eval`, `wandb`, and `vllm` separately. |
| Evolution config rejects its merge method or base model | Genome method is outside the fixed supported map, base model is missing for task-arithmetic variants, layer granularity does not divide the model, or SLERP uses filters/smoothing. | Validate these fields before allocating resources. Choose a supported method and a divisor of the actual layer count. |
| Evolution starts with no useful score or fails to evaluate | `tasks` is missing/empty, the LM-Eval task is not installed/discoverable, or `metric` is wrong. | Require at least one real task/metric pair, validate custom task search paths, and run only a bounded evaluator smoke test with approved local fixtures. |
| `buffered` or `serial` rejects `--in-memory` | In-memory mode is implemented only for the pool strategy. | Use on-disk mode for buffered/serial, or switch to pool after checking VRAM and fragile evaluator internals. |
| Candidates disappear or disk fills | On-disk mode stores resharded inputs, caches, and temporary merged models; storage may not be shared/fast enough. | Use a disposable, capacity-checked storage root, select pool for local compatibility, and disable final-model saving for a config-only pilot. Do not reuse a busy run directory. |
| Ray actors cannot place or GPUs disagree | `--num-gpus`, Ray visibility, PyTorch device, and strategy topology do not match. | Stop, compare visible accelerator counts, use a placement-compatible strategy, and route detailed model/device diagnosis to `model-io-and-architecture`. |
| `--vllm` fails or changes a working PyTorch environment | vLLM extra is absent or its pinned dependency set conflicts with the current accelerator stack. | Keep vLLM off for the baseline, isolate its environment, and verify a tiny evaluator before using it. Do not repair a shared environment automatically. |
| `--wandb` fails | `wandb` is absent, credentials/network are unavailable, or project/entity ownership is unclear. | Disable W&B for local validation. Enable it only after explicit credential and data-sharing approval; never commit tokens. |
| `--load-in-4bit` and `--load-in-8bit` are both set | CLI rejects the mutually exclusive quantization flags. | Select one or neither. Quantized evaluation also cannot use vLLM or in-memory mode and needs `bitsandbytes`. |
| Results are not reproducible or budget is exceeded | Model revisions, seed, extras, evaluator files, storage state, or CLI flags were not recorded; CMA-ES can exceed `max-fevals` by a generation. | Pin the environment, preserve YAML and `best_config.yaml`, record all flags and model revisions, and pair a small `max-fevals` with `--timeout`. |
| Search targets a prohibited benchmark | The task name matches a protected common-benchmark prefix. | Use a development/custom task or obtain the explicit benchmark acknowledgement required by the CLI. Do not optimize test-set performance casually. |

## Stop conditions

Stop before model execution when any required optional module, evaluator task,
GPU placement, storage capacity, model revision, or credential approval is
unknown. Missing `cma`, Ray, LM-Eval, vLLM, or W&B is an explicit optional gate;
it is not a reason to weaken core extension tests. Stop rather than guessing
when `trust-remote-code`, `allow-crimes`, external evaluator access, or data
sharing would change the risk boundary.
