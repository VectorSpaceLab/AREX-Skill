# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `unrecognized arguments: --output_dir` | the docs example uses a different spelling than the parser | use `--output-dir` with `tools.visualize_data` |
| Demo fails while loading weights | the checkpoint does not match the selected config family, or no checkpoint override was supplied | supply a matching `train.init_checkpoint` value and keep the config/checkpoint pair aligned |
| Demo opens a window instead of saving | no output target was given | add an explicit output file or directory |
| Multiple image inputs fail with a single file target | the source demo only treats an existing directory as a batch target | use one input at a time or create the output directory before running the demo |
| Saved video has an unexpected container or no x264 warning | OpenCV fell back to another codec | inspect the saved extension and use a writable `.mp4` or `.mkv` target |
| `tools.benchmark` import or help fails on `psutil` | benchmark imports `psutil` at module load time | install `psutil` or skip benchmark planning in that environment |
| `benchmark --task eval` aborts on an assertion | eval benchmarking is single-GPU and single-node only | keep `--num-gpus 1 --num-machines 1` |
| FLOPs or activation analysis fails | the workflow needs a checkpoint and sampled data, or the launcher was widened beyond one GPU | add the checkpoint override, keep `--num-inputs` bounded, and leave the launcher at one GPU |
| `visualize_data --source dataloader` never terminates | the training dataloader is effectively infinite | use it for spot checks and interrupt it manually after enough samples |
| `visualize_json_results` cannot map labels | the dataset name is not registered or the JSON category ids do not match the dataset metadata | register the dataset and verify the COCO/LVIS-style category mapping |
| MOT tracking looks unstable or random | the tracking route is sequence-dependent and carries state between frames | use one contiguous sequence from a single scene and reset between scenes |
| DINO demo hits a custom CUDA op error | the custom `MultiScaleDeformableAttention` extension is missing or incomplete | use a compatible non-custom-op model for the demo check, or repair the CUDA extension first |
