# Learning Data and Checkpoint Contracts

## Dataset preflight

Before training, write down the schema rather than relying on a loader's first
batch:

- episode id and time order;
- robot/task/simulator identity;
- observation keys and shapes, image dimensions/channels, dtype/range;
- action key, dimension, units, frame and gripper convention;
- reward/termination/truncation semantics when RL data is reused;
- camera names/order and calibration metadata;
- normalization statistics and train/validation split;
- source commit/config and any external asset/model identifiers.

Validate empty episodes, missing keys, inconsistent shapes, NaN/Inf, duplicate
timestamps, and episode boundary handling with a tiny fixture. Keep conversion
outputs separate from source data and report the format version.

## Checkpoint contract

A checkpoint is not only model weights. Depending on the route it may require:

- actor/policy weights;
- critic and target critic weights for RL resume;
- observation and critic-observation normalizer state;
- optimizer/scaler state when exact resume is required;
- task/robot/simulator/config identity;
- global step/epoch and policy preprocessing;
- camera and action unscaling configuration.

For FastTD3, the saved structure includes actor, qnet, qnet target,
`obs_normalizer_state`, `critic_obs_normalizer_state`, `config`, and
`global_step`. Load with an explicit device map and validate every key before
running evaluation. Do not silently ignore missing normalizer state.

## Evaluation assertions

At minimum assert:

1. checkpoint loads with the expected architecture and dtype;
2. normalization statistics are in eval/frozen mode;
3. task reset and camera keys match training;
4. action bounds and gripper/joint order are correct;
5. one deterministic inference step produces finite actions in range;
6. the reported backend and simulator match the run actually performed.
