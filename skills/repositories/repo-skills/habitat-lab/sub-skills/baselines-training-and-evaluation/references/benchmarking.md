# Benchmarking Guidance

Habitat 2.0 and Habitat 3.0 benchmark scripts are useful reference material, but they are expensive and data/simulator dependent. Treat them as adaptation templates unless the user explicitly asks to run them and has confirmed the assets, simulator backend, GPU/CPU resources, and runtime budget.

## Habitat 2.0 Benchmark Scripts

The Habitat 2 benchmark utilities compare user systems with Habitat 2.0 rearrangement benchmark results. The source benchmark flow requires:

- Habitat-Sim and Habitat-Lab installed with Bullet physics support.
- Habitat 2 benchmark assets, usually downloaded with `python -m habitat_sim.utils.datasets_download --uids hab2_bench_assets`.
- A benchmark episode file, either copied from downloaded assets or generated with the rearrangement episode generator.
- Benchmark runner and plotting scripts.

The original README describes a hardware context with dual Xeon CPUs and eight NVIDIA 2080 Ti GPUs, plus different process counts for single-GPU and multi-GPU runs. Results are therefore machine- and process-layout-sensitive.

## Habitat 3.0 Benchmark Scripts

The Habitat 3 benchmark utilities compare systems on Habitat 3.0 social/multi-agent scenarios. They require:

- Habitat-Sim and Habitat-Lab with Bullet physics support.
- Habitat 3 benchmark assets, commonly from `habitat_sim.utils.datasets_download --uids hab3_bench_assets` or a Hugging Face dataset clone.
- Correct symlinks or dataset paths for assets and episode datasets.
- Benchmark runner and plotting scripts.

These scripts are even more likely to depend on simulator assets, humanoid/robot URDFs, rendering support, and GPU/CPU process scheduling.

## Safe Adaptation Pattern

Instead of running benchmark shell scripts directly in an agent session, adapt their intent into a controlled command:

1. Read the benchmark README and identify required assets and simulator features.
2. Use `habitat-baselines --help` and the probe script to confirm the installed baseline config groups.
3. Compose the target config without training to catch Hydra errors first.
4. Override output paths to user-approved locations.
5. Reduce scale only for a smoke test, and label it clearly as a smoke test rather than a benchmark result.
6. Record the exact hardware/process/data choices when interpreting throughput or reward.

Example smoke-style adaptation:

```bash
python -u -m habitat_baselines.run \
  --config-name=social_nav/social_nav.yaml \
  benchmark/multi_agent=hssd_spot_human_social_nav \
  habitat_baselines.num_environments=1 \
  habitat_baselines.num_updates=1 \
  habitat_baselines.total_num_steps=-1 \
  habitat_baselines.num_checkpoints=1 \
  habitat_baselines.checkpoint_folder=checkpoints_smoke \
  habitat_baselines.tensorboard_dir=tb_smoke \
  habitat_baselines.video_dir=video_smoke
```

Only run this after confirming all referenced datasets and simulator assets exist.

## When To Refuse Or Defer Running

Defer benchmark execution and provide setup instructions when any of these are true:

- The user has not authorized a long GPU/CPU run.
- Required assets, scenes, episodes, or humanoid/robot files are missing.
- Habitat-Sim is unavailable or lacks required CUDA/physics/rendering support.
- The command would download large datasets without user approval.
- The benchmark shell script launches many processes, writes broad output directories, or assumes cluster scheduling.
- The user asks for paper/table-comparable numbers from different hardware.

## Interpreting Results

Benchmark throughput and reward curves are not just code correctness signals. They depend on:

- GPU model/count, CPU cores, memory bandwidth, and process binding.
- Number of environments and processes per GPU.
- Dataset split and scene/episode selection.
- Rendering mode, sensor resolution, and simulator backend.
- Whether DD-PPO/VER/distributed workers are actually enabled.

Use benchmark results to compare a controlled local setup against itself after changes. Avoid claiming equivalence to release numbers unless the hardware, data, command, and evaluation protocol match.
