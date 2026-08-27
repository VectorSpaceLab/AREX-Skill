# Resource and latency tuning

This reference covers hls4ml config knobs that change generated implementation tradeoffs. Treat every knob as a hypothesis until validated with the right evidence level.

- CPU `compile()`/`predict()` parity validates numerical behavior only.
- C simulation validates generated C++ behavior.
- FIFO depths, deadlock freedom, and resource utilization require vendor backend build/co-simulation/report evidence. Route those executions to `backends`.

## ReuseFactor

`ReuseFactor` controls how much arithmetic is reused across cycles. Lower values generally favor latency and parallelism; higher values generally reduce parallel resources but increase initiation interval/latency. It can be set at model, type, or name granularity:

```python
config["Model"]["ReuseFactor"] = 1
config["LayerType"]["Dense"]["ReuseFactor"] = 4
config["LayerName"]["dense1"]["ReuseFactor"] = 8
```

Layer-name values override layer-type and model defaults. Always re-run numerical parity after changing `ReuseFactor`, because different implementations can expose marginal precision choices.

## Strategy

`Strategy` chooses the layer implementation style. Common values include:

- `Latency`: more parallel, usually faster and larger.
- `Resource`: more reuse-oriented, usually smaller and slower.
- `distributed_arithmetic` or `da`: distributed-arithmetic implementation when available; the reuse factor must be 1.
- `Unrolled`: unrolled multiplication style, used by some hardware-aware optimization guidance before synthesis.

Examples:

```python
config["Model"]["Strategy"] = "Latency"
config["LayerName"]["dense1"]["Strategy"] = "Resource"
```

Backend constraints matter. For example, Intel-oriented Quartus/oneAPI paths are resource-strategy oriented, and oneAPI currently lacks tracing and external-weight support. If the chosen backend rejects a strategy, route the backend-specific failure to `backends`.

## BramFactor: external weight storage

`BramFactor` is a **model-level** threshold. Layers with more weights than the threshold can expose weights through an external BRAM-style interface rather than embedding them in the design.

```python
config["Model"]["BramFactor"] = 100
```

Important facts:

- It is not a per-layer key in the current config parser.
- A low threshold such as `0` can force simple-model weights into BRAM storage in supported backends.
- The advanced feature is documented for Xilinx/Catapult-style flows, while the Quartus backend also documents support; oneAPI explicitly does not support external weights.
- The generated top function gains weight-interface arguments when weights are externalized.
- The user is responsible for loading weights correctly in the final system.

Validation level:

- CPU parity can show that the generated model still predicts correctly with externalized weights.
- To claim a resource saving or integration-ready BRAM interface, inspect backend output or reports and route that evidence to `backends`.

## FIFO depth optimization

FIFO depth optimization is for `io_stream` designs where layer outputs are connected by streams. Conservative default depths can overuse BRAM/LUT resources. The optimization sizes FIFOs from RTL co-simulation occupancy.

High-level configuration pattern:

```python
flow = "vivado:fifo_depth_optimization"  # or "vitis:fifo_depth_optimization"
config["Flows"] = [flow]
hls4ml.model.optimizer.get_optimizer(flow).configure(profiling_fifo_depth=100_000)
```

Requirements and caveats:

- Use only with `IOType`/`io_type` set to `io_stream`.
- The documented and source-implemented production paths are Vivado and Vitis. Catapult has a registered backend flow, but do not assume parity with the Vivado/Vitis co-simulation documentation without backend evidence.
- `profiling_fifo_depth` must be a non-negative integer. The default source value is `100_000`.
- The optimizer first uses large FIFOs for profiling, runs synthesis/co-simulation, reads FIFO occupancy from VCD data, then sets each FIFO depth to the observed maximum plus one.
- If no FIFOs are implemented in BRAMs, the optimizer reports that no optimization is possible and suggests increasing `profiling_fifo_depth`.
- A successful FIFO-depth claim needs both reduced FIFO-depth data and a passing co-simulation/deadlock check. Do not claim success from config changes alone.

## Safe tuning loop

1. Keep a baseline config and representative validation data.
2. Change one knob at a time: precision, `ReuseFactor`, `Strategy`, `BramFactor`, or FIFO flow.
3. Run CPU `compile()`/`predict()` parity for every config edit.
4. Use profiling/trace when parity worsens.
5. For FIFO/resource claims, stop at a documented plan unless a backend toolchain run produced co-simulation/report evidence.
6. Record exactly which evidence supports each conclusion: parity, C simulation, co-simulation, or synthesis/report.
