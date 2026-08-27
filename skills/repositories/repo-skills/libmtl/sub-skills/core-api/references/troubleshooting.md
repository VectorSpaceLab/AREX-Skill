# core-api Troubleshooting

## Symptom → cause → fix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` or `TypeError` during `Trainer(...)` construction | Passing class objects instead of string names | Use `weighting='EW'` and `architecture='HPS'`. |
| `KeyError: 'arch_args'` or `KeyError: 'weight_args'` | Direct `Trainer` construction skipped `prepare_args` | Add both dictionaries explicitly, even if they are empty. |
| `UnboundLocalError` in `prepare_args` | Using an advertised but unwired optimizer or scheduler choice | Stick to `optim='adam'` or `optim='sgd'` and `scheduler='step'`. |
| `cuda:0` errors on a CPU-only host | The trainer is CUDA-first | Use a GPU-backed environment. |
| Unexpected output shape from `resnet18` or `resnet_dilated` | Backbones return features, not predictions | Add task-specific decoders or heads. |
| `MOML`, `FORUM`, or `AutoLambda` behave differently from the single-level methods | They use the trainer's bilevel path | Read the bilevel notes in `api-reference.md` and `configuration.md`. |

## What to check first

1. `LibMTL` imports successfully.
2. `torch.cuda.is_available()` is `True`.
3. `prepare_args` produced both `weight_args` and `arch_args`.
4. The requested weighting and architecture names exist in the exported module
   lists.

## Safe recovery path

If the API still fails after those checks, run `scripts/check_core_api.py`.
If that script succeeds, the problem is usually in the benchmark-specific task
setup rather than in the shared LibMTL API.
