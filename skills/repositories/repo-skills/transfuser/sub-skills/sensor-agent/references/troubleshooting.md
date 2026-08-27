# Sensor-Agent Troubleshooting

Start with the bundled static validator:

```bash
python scripts/validate_agent_config.py /path/to/team-config --json
```

It is safe to run without CARLA, PyTorch, a GPU, or model weights that can be
deserialized. It validates the directory schema, JSON fields, and checkpoint
containers but does not prove parameter compatibility.

## Failure Matrix

| Symptom | Likely cause | Safe diagnosis | Recovery |
| --- | --- | --- | --- |
| `ModuleNotFoundError: carla` | CARLA Python API is absent | Treat separately from model-side package imports | Install/mount the external CARLA 0.9.10.1 Python API that matches the server and Leaderboard stack; do not claim readiness from CUDA imports alone |
| Agent imports but evaluation cannot connect | Server is absent, wrong port, or version mismatch | Confirm a compatible external server exists without launching it from this bundle | Use the evaluation workflow to configure and launch CARLA explicitly; preserve the 0.9.10.1 compatibility target |
| `args.txt` not found | `TEAM_CONFIG` points to a file or wrong directory | Check that the argument is the containing directory | Place `args.txt` and all intended model `.pth` files together; pass that directory |
| JSON decode error | `args.txt` is not valid JSON | Run the validator for line/column detail | Restore the exact JSON emitted during training; do not convert it to shell syntax or Python repr |
| No `.pth` files found | Empty/wrong config directory | List only regular files with `.pth` suffix | Copy at least one trusted model state dict; do not download from this skill |
| Many models load unexpectedly or GPU OOM | Optimizer checkpoints or extra models also end in `.pth` | Count `.pth` files and sizes; remember every one becomes an ensemble network | Keep only intended model state dicts; move optimizer artifacts elsewhere or rename them without `.pth` |
| `torch.load`/archive error | Truncated, wrong-format, or untrusted checkpoint | Use static signature and size checks; compare artifact provenance/hash outside the runtime | Re-copy a trusted complete checkpoint; do not attempt inference with a damaged archive |
| Widespread missing/unexpected state-dict keys | Architecture fields differ from training, or keys were rewritten incorrectly | Compare `args.txt` against training provenance and inspect whether keys start with `module.` | Restore matching architecture fields; strip `module.` only for DDP-prefixed state dicts |
| Single-GPU checkpoint appears to load but behavior is nonsensical | Runtime unconditionally removed the first seven characters from unprefixed keys; `strict=False` hid the mismatch | Inspect key-prefix distribution and key-match coverage before loading | Remove/replace the unconditional rewrite with conditional `module.` normalization for trusted local code |
| DDP checkpoint keys all begin with `module.` | Expected DistributedDataParallel save format | Confirm the prefix is uniform | Strip exactly `module.` once; do not strip arbitrary seven-character prefixes |
| SyncBatchNorm parameter mismatch | `sync_batch_norm` disagrees with training metadata | Compare the saved training argument and module/key names | Set `sync_batch_norm` to the original value; conversion occurs before load |
| Model construction mismatch with no obvious prefix issue | Missing/wrong `backbone`, encoder architecture, `n_layer`, target-image, point-pillar, or velocity setting | Compare all architecture-critical fields, not only backbone | Use the checkpoint's original `args.txt`; runtime defaults differ from training defaults |
| `CUDA is not available`, invalid device, or CUDA OOM | Runtime hard-codes CUDA and maps loads to `cuda:0`; ensemble is too large or wrong visible device is selected | Check CUDA visibility and free memory outside this validator | Select one suitable visible GPU, free memory, or reduce ensemble count; there is no supported CPU inference fallback |
| OpenMMLab import/ABI error | PyTorch/CUDA/`mmcv-full` build mismatch | Compare versions and CUDA ABI | Use the observed compatible stack: PyTorch 1.12.1+cu113, `mmcv-full` 1.6.0, `mmdet` 2.25.0, `timm` 0.6.7; do not mix CPU `mmcv` with required compiled ops |
| `KeyError: lidar` | Non-latent backbone did not declare/receive LiDAR, or payload ID differs | Check exact backbone and sensor IDs | Restore lowercase `lidar` for `transFuser`, `late_fusion`, or `geometric_fusion`; omit only for exact `latentTF` |
| LiDAR is absent for `latentTF` | Often expected | Confirm the selected backbone is exactly `latentTF` and a dummy `[1,2,256,256]` tensor is created | Do not add a physical LiDAR just to satisfy generic assumptions |
| Point-pillar shape/index failure | Raw cloud schema, point count, range, or `use_point_pillars` differs from training | Compare raw payload shape and training args; do not voxelize before point pillars | Restore matching raw-cloud handling and config; keep the one-element tensor/count lists |
| Geometric-fusion forward argument failure | BEV-camera correspondence tensors are missing or wrong dtype/device | Confirm raw LiDAR is retained and correspondence arrays become batched CUDA int64 tensors | Rebuild the exact geometric preprocessing path rather than reusing late-fusion inputs |
| `KeyError` for RGB/GPS/IMU/speed | Sensor ID mismatch or bare payload rather than `(frame, data)` tuple | Compare IDs and wrapper shape against the sensor contract | Use exact lowercase IDs and Leaderboard tuple payloads |
| Empty/wrong camera crop | Camera geometry or crop config changed independently | Calculate both crop rectangles against the actual image dimensions | Restore coupled defaults or update both preprocessing stages consistently; never pad silently without retraining evidence |
| NaNs in target point or controls | Repeated compass/GPS NaNs or bad route input | The agent only replaces a NaN compass with zero; inspect upstream sensor stream | Repair sensor synchronization/data. Do not treat repeated zero substitution as a valid heading estimate |
| Route planner initialization crashes or route is empty | `_global_plan` was not provided, is malformed, or was exhausted | Verify `set_global_plan` ran and at least one usable GPS route point remains | Fix evaluator plan handoff before first `run_step`; do not synthesize arbitrary targets |
| Vehicle seems to hold commands every other frame | `action_repeat=2` behavior | Check step parity and LiDAR cadence | This is expected. Change only with a validated sensor-rate/control retuning |
| Vehicle remains stopped for about 55 seconds before creep | Default stuck threshold | Confirm processed-control cadence and speed threshold | Expected safety behavior; do not shorten solely to hide a bad checkpoint or route transform |
| Forced creep stops immediately | Front LiDAR occupancy or latent predicted box intersects safety region | Inspect safety-box coordinates and whether the vehicle is truly blocked | Clear false coordinate transforms/detections; do not disable the guard merely to force movement |
| Steering is reduced while braking/creeping | Steer damping is active | Confirm `steer_damping=0.5` and brake/stuck state | Expected. Tune only with simulator-backed safety tests |
| No debug images despite `SAVE_PATH` | Config `debug` is false, output path is unwritable, or the selected forward path does not emit the same visualization | Check that `SAVE_PATH` was set before import and that debug is enabled | Treat `SAVE_PATH` primarily as sensor-suite/output opt-in; do not use debug output absence as inference failure proof |

## Checkpoint Recovery Procedure

1. Stop before simulator launch if static validation fails.
2. Identify the checkpoint's training mode: DDP or single GPU.
3. Restore its exact training `args.txt`; do not reconstruct from runtime
   defaults.
4. Ensure the directory contains only model state dicts intended for one
   architecture-compatible ensemble.
5. For trusted checkpoints, inspect state-dict key names on CPU in a controlled
   environment. PyTorch 1.12 checkpoint deserialization uses pickle and is not
   safe for untrusted files.
6. Normalize keys conditionally: all `module.`-prefixed DDP keys lose that exact
   prefix; unprefixed single-GPU keys remain unchanged. Reject mixed forms until
   provenance is understood.
7. Compare matched, missing, and unexpected keys. Do not let `strict=False`
   convert a low-coverage load into a pass.
8. Only after configuration and key coverage are coherent, proceed to a bounded
   CARLA-backed smoke test through the evaluation workflow.

## Configuration Recovery Procedure

If `args.txt` is incomplete:

1. prefer the original training output over hand editing;
2. record the four-way backbone choice;
3. recover both image and LiDAR encoder names, even for paths where one sensor is
   omitted at runtime;
4. recover `n_layer`, target-point-image, point-pillar, velocity, and SyncBN
   fields;
5. note that training defaults and evaluation fallbacks differ;
6. validate again and treat warnings as failures for publication/evaluation
   preparation.

Do not use trial-and-error inference to guess architecture fields: repeated
large CUDA allocations and permissive state-dict loading can obscure the real
mismatch.

## External Block And Stop Conditions

Static preparation must stop short of an end-to-end success claim when any of
the following remain unresolved:

- CARLA 0.9.10.1 Python API or server is unavailable;
- the Leaderboard/scenario-runner stack is incompatible;
- CUDA inference is unavailable;
- checkpoint provenance or prefix normalization is uncertain;
- architecture key coverage has not been checked on a trusted checkpoint;
- required route/sensor streams have not been simulator-tested.

The prepared environment proved CUDA model-side imports only. The absent CARLA
module is a required-backend block, not an optional warning.
