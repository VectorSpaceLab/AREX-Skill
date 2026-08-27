# Setup and cluster troubleshooting

Use this reference after running the bundled probes and any safe `ray status` checks.

## Fast triage commands

From this sub-skill directory:

```bash
python scripts/rlinf_env_probe.py
python scripts/rlinf_env_probe.py --json
python scripts/render_cluster_plan.py path/to/config.yaml
ray status
```

If `render_cluster_plan.py` reports that PyYAML is unavailable, install or activate an environment with `pyyaml`, or inspect the YAML manually from the rendered error; the script fails gracefully without importing RLinf.

## Missing or wrong Ray

Symptoms:

- `ModuleNotFoundError: ray`.
- `ray: command not found`.
- Ray version differs across nodes.
- RLinf errors while waiting for nodes.

Actions:

1. Activate the intended Python environment on every node.
2. Run `python scripts/rlinf_env_probe.py --ray-status` on each node.
3. Verify Ray is importable and the CLI version is available; RLinf expects Ray `>=2.47.0`.
4. Stop and restart Ray if packages were installed or changed after `ray start`.
5. Ensure all nodes use compatible Python, Ray, Torch, and RLinf dependency versions.

## `RLINF_NODE_RANK` timing problems

Symptoms:

- Node rank 0 manager actors cannot be found.
- `cluster.num_nodes` waits forever or nodes appear with unexpected rank/order.
- Multi-node placement maps workers to the wrong machine.

Cause: Ray freezes environment variables at `ray start`. Exporting `RLINF_NODE_RANK` after Ray has already started is too late for Ray workers.

Fix:

```bash
ray stop
export RLINF_NODE_RANK=<correct_zero_based_rank>
ray start ...
```

Use unique ranks `0..N-1` and keep `cluster.num_nodes: N` in the YAML.

## Wrong head IP, port, or NIC

Symptoms:

- Worker `ray start --address` cannot connect.
- `ray status` on the head shows fewer nodes than expected.
- Distributed collectives hang or fail on multi-NIC hosts.

Actions:

1. Pick a head IP reachable from all workers; do not bind the head to `127.0.0.1` for multi-node use.
2. Confirm firewall/security-group rules allow the Ray port and required worker communication.
3. If machines have multiple network interfaces, export `RLINF_COMM_NET_DEVICES=<reachable_interface>` before `ray start` on every node.
4. Use the same Ray port in head and worker commands.
5. Confirm each node has joined the same cluster, not independent local Ray clusters.

## `cluster.num_nodes` and placement over-allocation

Symptoms:

- RLinf waits for nodes indefinitely.
- Placement parser says resource rank is out of range.
- Assertion about duplicate resource ranks or non-continuous process ranks.
- A component has fewer workers than expected.

Actions:

1. Compare `ray status` node/GPU totals with the YAML summary from `render_cluster_plan.py`.
2. Check `cluster.num_nodes` equals the actual number of joined Ray nodes.
3. In short form, verify global resource ranks exist in the homogeneous cluster.
4. In node-group form, verify `node_group` labels exist and `placement` ranks are local to that group.
5. Check process-rank segments are continuous from `0` to `N-1` and non-overlapping.
6. For model-parallel reasoning placement, ensure actor/rollout/reward/inference ranges are continuous and match tensor/pipeline/data-parallel sizes.

## Node-group and env-config errors

Symptoms:

- Reserved label assertions.
- Env var shape errors such as expecting one-key mappings.
- `python_interpreter_path` not used as expected.
- Different groups on the same physical node leak environment variables.

Actions:

1. Do not use reserved labels `cluster` or `node` for custom groups.
2. Write `env_vars` as a list of one-key maps:
   ```yaml
   env_vars:
     - GLOO_SOCKET_IFNAME: "eth0"
   ```
3. Ensure each `env_configs.node_ranks` list is a subset of its parent group's `node_ranks` and entries do not overlap.
4. Use `python_interpreter_path` only when Ray workers truly need different interpreters; otherwise use one activated environment before Ray starts.
5. Restart Ray after changing interpreter/env layout.

## Optional accelerator and backend packages

Symptoms:

- `torch.cuda.is_available()` is false when CUDA is required.
- `flash_attn`, `apex`, `transformer_engine`, `sglang`, or `vllm` fails to import.
- ROCm/Ascend/MUSA package or device runtime mismatch.

Actions:

1. Use `rlinf_env_probe.py` to separate core import readiness from optional backend readiness.
2. Do not treat missing optional packages as fatal unless the selected workflow requires them.
3. Match the install/platform choice to the hardware: NVIDIA/CUDA, AMD/ROCm, Ascend/CANN, or MUSA.
4. For MUSA, expect Torch/Torch-MUSA to come from the vendor training-suite image rather than ordinary PyPI wheels.
5. For Ascend, expect `torch-npu` to match the installed Torch version.
6. For AMD, ensure the ROCm version and Torch wheel index align.
7. If CUDA is required, verify driver visibility from both the shell and Python before debugging RLinf placement.

## Python and dependency issues

Symptoms:

- `ModuleNotFoundError: rlinf`.
- Wrong `rlinf` version imported.
- Hydra/OmegaConf import errors.
- A simulator env requires Python 3.10 but the active env is 3.11.

Actions:

1. Run `python scripts/rlinf_env_probe.py --json` and inspect `python.executable`, `sys.path_prefix`, package versions, and import locations.
2. If using a local source checkout only for inspection, pass `--repo-root` to the probe rather than mutating `PYTHONPATH` globally.
3. Align Python version with the selected env/model; RLinf core requires `>=3.10`, while some simulator stacks pin 3.10.
4. Avoid mixing agentic and embodied optional extras in one environment when dependency variants conflict.
5. Restart Ray after changing Python packages; Ray workers keep the environment captured at startup.

## Code sync pitfalls

Symptoms:

- Workers import old RLinf code or cannot import local changes.
- Ray spends a long time packaging code.
- Workers can import code but cannot find configs, models, or assets.

Actions:

1. Set `RLINF_CODE_WORKING_DIR=auto` before the driver initializes RLinf when nodes do not share the same code tree.
2. Keep large files out of the `rlinf/` package subtree; code sync packages that subtree only.
3. Put configs, datasets, checkpoints, model weights, and simulator assets on paths reachable by every node or shared storage.
4. Disable code sync when all nodes already have an identical installed package/tree.

## Direct Ray initialization conflict

Symptom: RLinf raises an error that Ray was initialized before `Cluster`.

Cause: User code or a helper created Ray objects or called `ray.init()` before RLinf's scheduler.

Fix: Remove the direct Ray initialization and let `Cluster(cluster_cfg=...)` initialize or attach to Ray. If the process is already polluted, restart the Python process and possibly Ray.

