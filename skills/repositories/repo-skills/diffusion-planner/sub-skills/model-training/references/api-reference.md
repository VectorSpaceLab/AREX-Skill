# Model-training API and tensor reference

This reference records the source-backed contracts for
`train_predictor.py`, `DiffusionPlannerData`, the normalizers, and
`Diffusion_Planner`. It is intentionally limited to the model-training handoff;
see the sibling skills for preprocessing and simulation.

## Configuration objects

### `train_predictor.py` argparse

`get_args()` parses the CLI, then immediately builds:

```python
args.state_normalizer = StateNormalizer.from_json(args)
args.observation_normalizer = ObservationNormalizer.from_json(args)
```

The important defaults are:

```text
future_len=80, time_len=21
agent_num=32, agent_state_dim=11, predicted_neighbor_num=10
static_objects_num=5, static_objects_state_dim=10
lane_num=70, lane_len=20, lane_state_dim=12
route_num=25, route_len=20, route_state_dim=12
batch_size=2048, learning_rate=5e-4, train_epochs=500
warm_up_epoch=5, save_utd=20, num_workers=4, pin_mem=True
encoder_depth=3, decoder_depth=3, num_heads=6, hidden_dim=192
encoder_drop_path_rate=0.1, decoder_drop_path_rate=0.1
alpha_planning_loss=1.0, diffusion_model_type=x_start
augment_prob=0.5, use_data_augment=True, use_ema=True
use_wandb=False, device=cuda, ddp=True, port=22323
```

Boolean values use the custom parser (`true/false`, `yes/no`, `1/0`, etc.).
`--pin-mem` and `--no-pin-mem` are normal action flags. The script does not
check that `batch_size` is divisible by the DDP world size.

The model consumes a config-like object with all of those attributes plus
`state_normalizer`, `observation_normalizer`, and (for `Config`) `guidance_fn`.
A training-style construction is:

```python
from diffusion_planner.model.diffusion_planner import Diffusion_Planner
model = Diffusion_Planner(args).to(args.device)
```

For a checkpoint consumer, construct `Config(args_json, guidance_fn)` first and
pass that object instead. `hidden_dim % num_heads == 0` is required by PyTorch
multi-head attention.

### `Config(args_file, guidance_fn)`

`diffusion_planner.utils.config.Config` loads JSON with `json.load`, assigns
all keys as attributes, rebuilds `StateNormalizer` from serialized `mean/std`,
rebuilds `ObservationNormalizer` tensors for each observation key, and stores
the supplied guidance callback. A training-generated `args.json` is the
intended companion to a checkpoint. Do not expect a `.pth` to contain model
hyperparameters.

## Dataset contract

`DiffusionPlannerData(data_dir, data_list, past_neighbor_num,
predicted_neighbor_num, future_len)` loads a JSON list with `openjson`, then
opens `os.path.join(data_dir, data_list[idx])` with `mmengine.fileio`. It returns
a tuple in exactly this order:

```text
0 ego_current_state
1 ego_future_gt (= ego_agent_future)
2 neighbor_agents_past[:past_neighbor_num]
3 neighbors_future_gt (= neighbor_agents_future[:predicted_neighbor_num])
4 lanes
5 lanes_speed_limit
6 lanes_has_speed_limit
7 route_lanes
8 route_lanes_speed_limit
9 route_lanes_has_speed_limit
10 static_objects
```

Default source shapes and the corresponding batch shapes are:

| tuple item | per-record | batch | notes |
|---|---:|---:|---|
| ego current | `(10,)` | `(B,10)` | first 4 are x/y/cos/sin |
| ego future | `(80,3)` | `(B,80,3)` | x/y/heading before conversion |
| neighbor past | `(32,21,11)` | `(B,32,21,11)` | 8 numeric channels + 3 type channels |
| neighbor future | `(10,80,3)` after slice | `(B,10,80,3)` | original file may contain up to 32 |
| lanes | `(70,20,12)` | `(B,70,20,12)` | first 8 geometry + 4 traffic |
| lane speed/availability | `(70,1)` | `(B,70,1)` | separate tensors |
| route lanes | `(25,20,12)` | `(B,25,20,12)` | decoder route encoder uses first 4 |
| route speed/availability | `(25,1)` | `(B,25,1)` | carried through input dict |
| static objects | `(5,10)` | `(B,5,10)` | zero rows are padding |

The dataset class does not validate keys or shapes. Validate before launching
workers. `future_len` is used as a model/loss contract but the dataset does not
slice ego future; a mismatch reaches the loss/model later.

## Training input preparation

`train_epoch` moves observation fields to `args.device`, optionally applies
`StatePerturbation`, converts ego and neighbor headings from radians to
`[cos(heading), sin(heading)]`, zeros padded neighbor futures, and applies
`args.observation_normalizer` to the observation dictionary.

The model input dictionary is:

```python
{
  "ego_current_state":       (B, 10),
  "neighbor_agents_past":    (B, agent_num, time_len, 11),
  "lanes":                   (B, lane_num, lane_len, 12),
  "lanes_speed_limit":       (B, lane_num, 1),
  "lanes_has_speed_limit":   (B, lane_num, 1),
  "route_lanes":             (B, route_num, route_len, 12),
  "route_lanes_speed_limit": (B, route_num, 1),
  "route_lanes_has_speed_limit": (B, route_num, 1),
  "static_objects":          (B, static_objects_num, 10),
}
```

`diffusion_loss_func` receives ego future `(B,T,4)`, neighbor future
`(B,N,T,4)`, and a neighbor mask `(B,N,T)`; it forms current+future
trajectories `(B,1+N,1+T,4)`, normalizes future states with
`StateNormalizer`, samples `t` in `(0.001, 1)`, and adds Gaussian noise.
The model receives the resulting `sampled_trajectories` and `diffusion_time`.

## Normalizers

`normalization.json` has two roles:

- `ego` and `neighbor`: four-channel future state statistics used by
  `StateNormalizer`;
- all other sections: observation statistics used by
  `ObservationNormalizer`.

For the checked-in file, future state mean/std are `[10,0,0,0]` and
`[20,20,1,1]`. `StateNormalizer.from_json` repeats those arrays for ego plus
`predicted_neighbor_num` trajectories, so its tensors are effectively
`(1+N,1,1,4)` broadcast over `(B,1+N,T,4)`. It does not normalize current
states.

`ObservationNormalizer` skips unknown keys, normalizes known keys, and resets
rows whose last dimension is entirely zero back to zero. It does not infer a
missing feature or broadcast a wrong vector length safely. A normalizer file
from a different model layout is a hard incompatibility.

## Model modules

`Diffusion_Planner` is an `nn.Module` with:

1. `Diffusion_Planner_Encoder` → `Encoder`:
   - `AgentFusionEncoder`: MLP-Mixer over each agent's `time_len` history,
     then type embedding and projection to `hidden_dim`;
   - `StaticFusionEncoder`: per-static-object projection;
   - `LaneFusionEncoder`: MLP-Mixer over lane points plus speed-limit and
     traffic embeddings;
   - `FusionEncoder`: `encoder_depth` self-attention blocks over
     `agent_num + static_objects_num + lane_num` tokens, with padding masks.
2. `Diffusion_Planner_Decoder` → `Decoder`:
   - route MLP-Mixer encoder over flattened `route_num * lane_len` route points;
   - DiT trajectory projection, ego/neighbor type embeddings, timestep
     embedding, self-attention and cross-attention blocks;
   - a `VPSDE_linear(beta_min=0.1, beta_max=20.0)` diffusion process.

The DiT output dimension is `(future_len + 1) * 4` per agent. `x_start` emits
clean-state predictions; `score` emits a score scaled by the SDE marginal
standard deviation.

## Forward outputs

Training mode (`model.train()` and the input has sampled trajectories):

```text
encoder_outputs["encoding"]: (B, agent_num + static_objects_num + lane_num, hidden_dim)
decoder_outputs["score"]:   (B, 1 + predicted_neighbor_num, 1 + future_len, 4)
```

Evaluation mode (`model.eval()`): the decoder initializes current states at
index 0 and Gaussian noise for future points, samples with `dpm_sampler`,
then returns:

```text
decoder_outputs["prediction"]: (B, 1 + predicted_neighbor_num, future_len, 4)
```

Predictions are inverse-normalized `[x,y,cos,sin]` states. The first trajectory
is ego; following trajectories are neighbors, including zero-padded/masked
ones. The sampler uses 10 DPM steps, order 2, `dpmsolver++`, multistep
`logSNR`, `denoise_to_zero=True`, and an intermediate constraint that preserves
current states.

## Checkpoint API

`save_model` writes:

```python
{
  "epoch": epoch + 1,
  "model": model.state_dict(),
  "ema_state_dict": ema.state_dict(),
  "optimizer": optimizer.state_dict(),
  "schedule": scheduler.state_dict(),
  "loss": train_loss,
  "wandb_id": wandb_id,
}
```

It writes both a descriptive epoch file and `latest.pth` with `mmengine.fileio`.
`resume_model(path, ...)` appends `/latest.pth`; pass the run directory. It
accepts either a dictionary containing `model` or a bare state dict, and treats
optimizer/scheduler/epoch/W&B/EMA keys as optional. Always compare `args.json`
with the requested model dimensions before loading.
