# Model and training behavior

The source defines two paired push/grasp fully convolutional networks. Both
consume the same RGB and depth heightmaps, but their output interpretation and
training target differ.

## Network and rotation contract

- `reactive_net` and `reinforcement_net` each build four DenseNet-121 trunks:
  push-color, push-depth, grasp-color, and grasp-depth. The paired color/depth
  features are concatenated for each primitive and passed through its own
  branch.
- Both classes set `num_rotations = 16`. A volatile forward evaluates indices
  `0..15`, spaced by `360/16 = 22.5` degrees. The input is rotated before the
  trunk and the branch output is rotated back before upsampling. A training
  forward evaluates one selected rotation to save memory; grasp backprop also
  evaluates the opposite index `(rotation + 8) % 16` because grasping is
  treated as symmetric.
- Reactive push and grasp heads emit three class channels. The source comments
  identify class 0 as the desired push/grasp, class 1 as no-change/failed
  outcome, and class 2 as ignored/no-loss. `trainer.forward` applies softmax
  and returns the class-0 affordance map.
- Reinforcement push and grasp heads emit one scalar map each. `trainer.forward`
  returns raw values interpreted as Q predictions; it does not apply softmax.
  The optimizer is SGD with learning rate `1e-4`, momentum `0.9`, and weight
  decay `2e-5`. Reactive heads use weighted cross entropy; reinforcement uses
  unreduced Smooth L1/Huber loss at the selected action mask.

The constructors request `pretrained=True` for each DenseNet. If matching
weights are not already cached, model construction can initiate a network
fetch. This is a side effect, not a safe import guarantee. Never infer that a
snapshot is self-contained merely because it contains the task heads: the
trunks may also need to match the historical state-dict layout.

## RGB-D preprocessing

The trainer's `forward(color_heightmap, depth_heightmap, ...)` expects an RGB
array `(H,W,3)` and a depth array `(H,W)`. The geometry route owns how those
heightmaps were projected; this route records only the model boundary:

1. Nearest-neighbor resize by a factor of two: color uses zoom `[2,2,1]`,
   depth uses `[2,2]`.
2. Compute a square rotation canvas from the doubled height, round its diagonal
   up to a multiple of 32, and zero-pad both arrays symmetrically. Zero is the
   value used for invalid/empty depth after the main loop replaces NaNs.
3. Scale color by `255`, then normalize channels with ImageNet statistics:
   mean `[0.485, 0.456, 0.406]`, standard deviation `[0.229, 0.224, 0.225]`.
4. Replicate the depth plane to three channels and normalize each channel with
   mean `0.01` and standard deviation `0.03` (meters).
5. Form a batch of one and permute to torch `(1,3,H,W)` for both modalities.

Saved heightmap depth is quantized in the logger at `1e-5` meters. Replay
reconstructs it by dividing the uint16 image by `100000`. Do not feed raw
camera integer depth to the trainer without the upstream scale and unit
conversion.

## Output indexing and action selection

The conceptual output contract is one spatial map per rotation:

```text
push_predictions[rotation, y, x]
grasp_predictions[rotation, y, x]
best_pix_ind = (rotation, y, x)
```

The main action thread computes each map's global maximum. It defaults to
`grasp`; unless `--grasp_only` is set, it chooses push when the best push score
exceeds the best grasp score. In testing with the reactive method only, the
push score must exceed *twice* the grasp score. Training and reinforcement
testing use the ordinary greater-than comparison. With exploration enabled,
the chosen primitive is replaced by a random push/grasp choice with probability
`explore_prob`.

The selected `(y,x)` indexes the valid depth heightmap. The main code maps
`x` and `y` into workspace coordinates using the heightmap resolution, while
rotation is converted to `rotation * 22.5` degrees. A push adjusts its z
position to the maximum local depth in a small finger-width safety window;
physical motion and the geometry of that adjustment belong to the sibling
routes. Keep `rotation` as the first index and do not swap x/y when consuming
saved actions.

The literal historical crop uses Python-2-era division expressions and fixed
backprop label sizes (`320x320` output canvas with a `224x224` action area).
The intended behavior is a map aligned to the source heightmap, but exact
array dimensions must be checked against the pinned interpreter and torch
stack. Modern Python 3 can turn slice bounds in the reactive branch into
floats, and current torch/torchvision removed or changed several APIs used by
this code (`Variable` volatile behavior, old upsampling calls, and legacy
constructor arguments). Therefore do not claim a modern full forward/training
loop from import success alone; use this output contract for inspection and
stop on a shape or slice mismatch.

## Reward and label semantics

### Reactive

`get_label_value` returns a binary label and logs the same value as the
reactive reward value:

- push: label `1` when no depth change is detected, otherwise `0`;
- grasp: label `1` when the grasp fails, otherwise `0`.

The selected pixel is labeled while the rest of the loss canvas is filled with
class `2` (ignored by the class weighting). This is supervised classification
from self-generated outcomes, not a discounted Q target. A higher returned
class-0 affordance means the network predicts the desired outcome, even though
the logged binary label uses `0` for success/change.

### Reinforcement

For the preceding primitive, `get_label_value` computes:

- push immediate reward `0.5` when depth change is detected, else `0`;
- grasp immediate reward `1.0` on success, else `0`;
- future reward `0` when there is neither change nor a successful grasp;
  otherwise run a volatile next-state forward and take the maximum push/grasp
  Q value;
- target `current_reward + gamma * future_reward`, where `gamma` is
  `--future_reward_discount` (default `0.5`). If the primitive is push and
  `--push_rewards` is absent, the immediate push term is deliberately removed,
  leaving `gamma * future_reward`.

The reward log records the immediate reward, while the label log records the
training target. A reinforcement target is therefore not interchangeable with
a reactive label or with an evaluation metric.

## Exploration, replay, and heuristics

- Training starts with `explore_prob = 0.5`. Without decay it stays at `0.5`;
  with `--explore_rate_decay` it is `max(0.5 * 0.9998**iteration, 0.1)`.
  Testing starts at zero and never updates it. The `is-exploit` log stores `1`
  for exploitation and `0` for an exploration choice.
- `--experience_replay` is training-only. After a transition, the code seeks a
  prior transition with the same primitive and an opposite outcome category,
  ranks candidates by prediction/target surprise, samples with a power-law
  bias, reloads the saved heightmaps, and backpropagates the sampled action.
  It skips replay when there are not enough prior samples. Missing paired image
  files or short logs are hard resume/data failures, not reasons to fabricate a
  replay sample.
- `--heuristic_bootstrap` invokes `push_heuristic` or `grasp_heuristic` after
  two consecutive no-change outcomes for that primitive. The heuristics scan
  the same 16 rotations, use depth shifts of 25 pixels and a `0.02` meter
  difference, then smooth candidate areas with a 25x25 kernel. They are a
  fallback and the source warns they can reduce final performance. The
  `use-heuristic` log records whether one was used.

These features affect data collection and target generation. They do not make
an unavailable simulator, camera, or robot safe or available.

## CPU and CUDA behavior

`Trainer` selects CUDA when `torch.cuda.is_available()` and `--cpu` is absent;
otherwise it uses CPU. On CUDA, model, loss, inputs, and label tensors are
moved explicitly. `--cpu` is the supported override and is the correct first
choice for parser/log checks, but the README reports that training can take
minutes per iteration on CPU rather than seconds on a GPU. A bounded CUDA
probe, when available through the root environment helper, is optional
compatibility evidence only. It does not validate a full forward with
historical APIs or a loaded snapshot.
