# Evaluation and deployment troubleshooting

| Symptom | Likely cause | Remedy |
|---|---|---|
| Benchmark cannot import | External simulator or benchmark package is absent | Classify as optional external runtime; install its documented environment separately and verify versions before judging Dexbotic. |
| Checkpoint loads but task fails | Task-specific prompt, camera, action space, or norm stats mismatch | Compare the deployment manifest with the training/evaluation config. |
| Robot receives no action | Server/bridge URL, port, or network namespace mismatch | Check server health from the bridge host, then inspect bridge logs; do not attach actuators during this diagnosis. |
| Robot moves incorrectly | Wrong action mode, non-delta mask, padding, gripper convention, or camera order | Freeze control, query capabilities, and compare exact action metadata. |
| Jitter/latency | FPS mismatch, chunk aggregation, image preprocessing, or network delay | Measure each stage independently; adjust only after recording the checkpoint contract. |
| DOS-W1 dimensionality error | 14D joint state or 32D model padding was not preserved | Verify indices `[6, 13]`, padding, and norm stats. |
| XLeRobot bad motion | 16D non-delta mask or wheel/head dimensions differ | Validate `[5, 11, 12, 13, 14, 15]` for the documented workflow and confirm the target config. |
| Navigation memory leaks across episodes | Reset-memory flag or session boundary missing | Call the navigation-specific reset path and preserve episode-first-frame metadata. |
| Video/state timestamps disagree | Conversion assumed row index despite dropped frames | Reconcile timestamp/frame mapping and regenerate JSONL; do not patch frame indices by eye. |
| External bridge script is unsafe to run | It opens hardware/network resources | Keep it reference-only and use a no-op/captured-input harness. |
