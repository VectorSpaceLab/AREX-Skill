# Backend Workflows

## CPU SA

Direct command:

```bash
quip-miner cpu --validator ws://127.0.0.1:9944 --num-cpus 4 --signer-key ~/.quip-miner/signing.json
```

Config shape:

```toml
[cpu]
num_cpus = 4
# mempool = false
```

CPU workers use simulated annealing and are the safest default for development and parser/config verification. CPU mempool defaults on.

## CUDA / Local NVIDIA GPU

Install with the CUDA extra and verify CuPy can allocate:

```bash
python -m pip install 'quip-protocol[cuda]'
python - <<'PY'
import cupy as cp
print(cp.cuda.runtime.getDeviceCount())
cp.zeros(1)
PY
```

Direct command:

```bash
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend local --signer-key ~/.quip-miner/signing.json
```

Config shape:

```toml
[gpu]
utilization = 100
yielding = false
sms_per_nonce = 4
# mempool = false

[cuda.0]
[cuda.1]
```

`utilization` and `yielding` tune GPU scheduling. `sms_per_nonce` is CUDA-specific. GPU mempool defaults on.

## Apple Metal

Install with the Metal extra on Apple Silicon macOS:

```bash
python -m pip install 'quip-protocol[metal]'
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend metal --signer-key ~/.quip-miner/signing.json
```

Config shape:

```toml
[metal]
utilization = 100
yielding = true
active_util = 85
idle_after_s = 60
```

When `yielding` is on, the adaptive governor caps GPU occupancy while the user is active and can pause for battery/critical thermal conditions. Idle/headless runs can go full speed. Total reads and sweeps are preserved; the cap controls concurrent threads per command buffer.

There is no CPU fallback for live Metal. A Linux import check does not prove Metal runtime.

## Modal Cloud GPU

Modal is optional and requires the `modal` package and authentication:

```bash
pip install modal
modal token new
quip-miner gpu --validator ws://127.0.0.1:9944 --gpu-backend modal --signer-key ~/.quip-miner/signing.json
```

Config shape:

```toml
[modal]
gpu_type = "a10g"
```

If `GPU.modal_sampler.GPU_AVAILABLE` is false, the package imported but live Modal execution is unavailable. Do not treat that as a local GPU failure.

## D-Wave QPU

D-Wave credentials come from environment variables such as `DWAVE_API_KEY`, never TOML secrets.

Direct command:

```bash
quip-miner qpu --validator ws://127.0.0.1:9944 --qpu-type dwave --daily-budget 30s --signer-key ~/.quip-miner/signing.json
```

Config shape:

```toml
[dwave]
daily_budget = "30m"
min_block_budget = "90s"
budget_cap = "30m"
qpu_initial_budget = "min"
solver = "Advantage2_system1"
region = "na-west-1"
# mempool = true
```

QPU budget durations accept units such as `30s`, `5m`, `2h`, and `1d`. QPU mempool defaults off because paid samples are opt-in. Jobs dispatch idle-only and do not preempt in-flight QPU work.

## Gate-model QPU Providers

Supported CLI choices include `ibm`, `ionq`, `pasqal`, `braket`, and `origin`. Treat these as provider-specific optional alternatives unless the user provides the necessary packages, tokens, and live-run approval.

## Production Config vs Direct Commands

For production, prefer:

```bash
quip-miner --config config.toml
```

Direct backend subcommands are still useful when generating or testing command lines. Do not mix a backend inventory section with conflicting direct CLI inventory flags.
