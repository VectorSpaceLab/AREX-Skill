# Alpamayo R1 inference workflows

## 1. Run one sample clip end to end

Use the bundled smoke script first whenever possible:

```bash
python scripts/run_inference_smoke.py --clip-id 030c760c-ae38-49aa-9ad8-f5650a545d26 --t0-us 5100000 --num-traj-samples 1
```

The scripted path mirrors the repository example:

```python
import torch
import numpy as np

from alpamayo_r1.models.alpamayo_r1 import AlpamayoR1
from alpamayo_r1.load_physical_aiavdataset import load_physical_aiavdataset
from alpamayo_r1 import helper

clip_id = "030c760c-ae38-49aa-9ad8-f5650a545d26"
data = load_physical_aiavdataset(clip_id, t0_us=5_100_000)
messages = helper.create_message(data["image_frames"].flatten(0, 1))

model = AlpamayoR1.from_pretrained("nvidia/Alpamayo-R1-10B", dtype=torch.bfloat16).to("cuda")
processor = helper.get_processor(model.tokenizer)

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=False,
    continue_final_message=True,
    return_dict=True,
    return_tensors="pt",
)

model_inputs = helper.to_device(
    {
        "tokenized_data": inputs,
        "ego_history_xyz": data["ego_history_xyz"],
        "ego_history_rot": data["ego_history_rot"],
    },
    "cuda",
)

torch.cuda.manual_seed_all(42)
with torch.autocast("cuda", dtype=torch.bfloat16):
    pred_xyz, pred_rot, extra = model.sample_trajectories_from_data_with_vlm_rollout(
        data=model_inputs,
        top_p=0.98,
        temperature=0.6,
        num_traj_samples=1,
        max_generation_length=256,
        return_extra=True,
    )
```

Key reminders:

- `num_traj_samples=1` is the safest default for GPU memory.
- `sample_trajectories_from_data_with_vlm_rollout` consumes `tokenized_data["input_ids"]`, so rebuild the tokenized input if you want to call it again.
- The returned reasoning text lives in `extra["cot"]`, `extra["meta_action"]`, and `extra["answer"]`.

## 2. Inspect Chain-of-Causation text

`extra["cot"]` is the fastest way to inspect the reasoning trace per sampled trajectory.

```python
print("Chain-of-Causation (per trajectory):\\n", extra["cot"][0])
```

If the trace is empty, revisit the chat-template construction and confirm that the processor uses the Alpamayo tokenizer.

## 3. Compare predicted trajectories with ground truth

Use the local ego frame from the loader and compare the `xy` coordinates only:

```python
gt_xy = data["ego_future_xyz"].cpu()[0, 0, :, :2].T.numpy()
pred_xy = pred_xyz.cpu().numpy()[0, 0, :, :, :2].transpose(0, 2, 1)
diff = np.linalg.norm(pred_xy - gt_xy[None, ...], axis=1).mean(-1)
min_ade = diff.min()
```

Because the model samples trajectories, the exact minADE varies across runs even with the same seed.

## 4. Notebook-style visualization

The notebook-style route is useful when you want to inspect frames and trajectory overlays together. It assumes the notebook extras are installed; if they are not, stay with the smoke script and textual minADE / CoC inspection.

```python
import mediapy as mp
import matplotlib.pyplot as plt
import numpy as np

mp.show_images(data["image_frames"].flatten(0, 1).permute(0, 2, 3, 1), columns=4, width=200)

def rotate_90cc(xy):
    return np.stack([-xy[1], xy[0]], axis=0)

gt_xy = data["ego_future_xyz"].cpu()[0, 0, :, :2].T.numpy()
gt_xy_rot = rotate_90cc(gt_xy)

for i in range(pred_xyz.shape[2]):
    pred_xy = pred_xyz.cpu()[0, 0, i, :, :2].T.numpy()
    pred_xy_rot = rotate_90cc(pred_xy)
    plt.plot(*pred_xy_rot, "o-", label=f"Predicted Trajectory #{i + 1}")

plt.plot(*gt_xy_rot, "r-", label="Ground Truth Trajectory")
plt.ylabel("y coordinate (meters)")
plt.xlabel("x coordinate (meters)")
plt.axis("equal")
plt.legend(loc="best")
```

The rotation helper is only for display convenience; the underlying trajectory tensors remain in the ego frame at `t0`.

## 5. Fallback when flash-attn is not viable

Keep the CUDA path as the primary route. If flash-attn is unavailable or incompatible in your environment, re-load with SDPA on the model config and keep the rest of the workflow unchanged.

```python
# Primary path: flash_attention_2
model = AlpamayoR1.from_pretrained("nvidia/Alpamayo-R1-10B", dtype=torch.bfloat16)

# Fallback path when flash-attn is not viable
model = AlpamayoR1.from_pretrained(
    "nvidia/Alpamayo-R1-10B",
    dtype=torch.bfloat16,
    attn_implementation="sdpa",
)
```

Use the fallback only when you cannot make flash-attn work.
