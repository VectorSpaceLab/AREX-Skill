# Test and CI Selection

Use this reference to choose a focused validation set for TorchRL code edits. It is not a replacement for area-specific workflow knowledge; ask the relevant API sub-skill for behavior-specific tests, then use this file for maintainer and CI coverage.

## Fast triage from touched paths

Run the bundled helper from any current directory with the files you changed:

```bash
# From the development-and-testing sub-skill directory:
python scripts/list_relevant_tests.py torchrl/envs/foo.py test/envs/test_bar.py
```

The helper only uses the paths passed to it and prints likely test targets, CI concerns, and notes. It does not inspect a repository checkout unless you pass repository paths to it.

## Focused test selection by area

Prefer the smallest meaningful pytest subset first, then widen when failures, interactions, or CI risk require it.

| Touched area | Focused candidates | Notes |
| --- | --- | --- |
| `torchrl/envs/`, `test/envs/` | `test/envs/test_env_base.py`, `test/envs/test_step_mdp.py`, relevant transform tests | Include specs, reset/rollout, done/truncated layout, nested keys. |
| `torchrl/envs/transforms/`, transform configs | `test/transforms/`, selected env tests | Add nested-key coverage when transform keys accept `NestedKey`. |
| `torchrl/collectors/` | collector tests plus evaluator tests | Process-spawning collector tests are often serial/quarantined in CI. |
| `torchrl/data/replay_buffers/` | `test/rb/test_rb_core.py`, `test/rb/test_prioritized.py`, storage/sampler-specific files | Include sample shape, priority update, memmap cleanup, device/storage-device behavior. |
| `torchrl/modules/` | actor, distribution, RNN, multi-agent model tests | Include spec projection, distribution shape, recurrent state/primer tests. |
| `torchrl/objectives/` | algorithm-specific `test/objectives/` files | Exercise loss forward keys, `set_keys()`, value estimators, target updates. |
| `torchrl/trainers/algorithms/` or configs | `test/test_configs.py` plus area tests | Check Hydra instantiation and class/config parity. |
| `torchrl/services/` | `test/services/` | Service tests may spawn processes or need Ray depending on backend. |
| LLM/VLA paths | `test/llm/`, `test/data/test_vla.py`, `test/objectives/test_vla.py` as provisioned | Many dependencies are optional; isolate CPU schema tests from serving/model downloads. |
| docs reference only | docs build or doc checker scripts when available | Also run relevant code examples if behavior changed. |
| benchmarks or hot paths | matching `benchmarks/` file and focused functional tests | Benchmarks supplement correctness tests; they do not replace them. |
| SOTA algorithms | `sota-implementations/<algo>/`, `sota-check/`, and the SOTA smoke list | New algorithms need runnable SOTA wiring in addition to unit tests. |

## GPU marker policy

TorchRL CI splits CPU and GPU tests with mutually exclusive marker filters:

- CPU jobs run tests with `-m 'not gpu'`.
- GPU jobs run tests with `-m gpu`.

Therefore every CUDA-only test that uses a skip condition such as `not torch.cuda.is_available()`, `not torch.cuda.device_count()`, `_has_cuda`, `_has_triton`, or another CUDA/Triton-only gate must also have `pytest.mark.gpu` at function, class, or module scope.

Good pattern:

```python
@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
def test_cuda_specific_behavior():
    ...
```

Do not add `pytest.mark.gpu` to a test that meaningfully covers CPU and GPU through parametrization or fallback logic, for example a test that chooses CPU when CUDA is unavailable. Those tests must remain visible to CPU CI.

Dedicated GPU-runner workflows that pin exact files or `-k` selectors may not strictly require the marker, but adding it is harmless and keeps policy consistent.

### Static marker check

Use the bundled checker before finalizing CUDA/Triton tests:

```bash
# From the development-and-testing sub-skill directory:
python scripts/check_gpu_marker_policy.py test/my_cuda_test.py
```

It flags likely CUDA-only skip conditions missing a visible `pytest.mark.gpu` marker. Review findings manually because static checks can be conservative around custom skip variables.

## PR-gated labels

Two expensive suites do not run on ordinary pull requests unless a label is present before a commit or workflow rerun.

### `ci/olddeps`

Add `ci/olddeps` when a change uses a torch API, keyword argument, behavior flag, or dependency behavior that may not exist in the oldest supported stable stack. If in doubt, use the label. Without it, compatibility breakage may land and only fail later on main or nightly.

### `ci/optdeps`

Add `ci/optdeps` when a change touches optional-dependency integrations or their import paths. Ordinary PRs get an optional-dependencies smoke that checks the environment and imports, not the full long suite.

Apply labels before pushing a commit or rerunning CI; labeling alone does not retrigger workflows.

## CI shard behavior to remember

The Linux CI script separates:

- transform shard;
- process-spawning quarantine including collectors, parallel envs, services, inference server, loggers, and related tests;
- bulk tests that can use xdist on CPU;
- distributed tests, which are GPU-only in CI;
- olddeps shards;
- optional-dependency full versus smoke jobs.

A local command that passes under a single pytest invocation may still fail in a serial process-spawning shard, in xdist, or under GPU marker filtering. Reproduce the closest shard behavior when diagnosing flakes or deselection.

## Minimum local run pattern

1. Run the direct tests covering changed files.
2. Run the nearest API workflow smoke or unit subset from the relevant sub-skill.
3. Run `check_gpu_marker_policy.py` on changed tests when CUDA, Triton, device-count, or backend skip conditions appear.
4. If config docs changed, run focused config tests and doc/static checks.
5. If optional integrations changed, plan `ci/optdeps`; if new torch APIs changed, plan `ci/olddeps`.

Record optional backend gaps explicitly. CPU-only local success does not verify CUDA kernels, Triton recurrent paths, distributed services, model-serving integrations, simulator stacks, or rendering/video codecs.
