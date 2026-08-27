# Training troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `use_stage1_dataset and offload cannot both be True` | Conflicting data/offload path | Disable one of the two settings |
| `force_rebuild must be True when single_res is enabled` | Cache metadata is stale for the fixed resolution | Set `force_rebuild: true` for the preflight run |
| Validation window/list length assertion | `validation_latent_window_size` or `validation_stream_chunk_size` has more than one entry | Collapse both validation lists to single-item lists |
| `dataset_sampling_ratios is only supported when use_stage1_dataset=True` | Ratio fields were set for the wrong dataset mode | Enable stage-1 dataset mode or remove ratios |
| `Duplicate dataset name` | Two data roots collapse to the same stripped basename | Rename or de-duplicate the roots |
| MPS bf16 error | MPS does not support bf16 mixed precision | Use fp16 or fp32 on MPS, or switch to CUDA |
| `xformers is not available` | Optional xFormers path enabled without the package | Install xFormers or disable the flag |
| `npu flash attention requires torch_npu` | NPU-specific flag enabled on non-NPU environment | Install torch_npu in an NPU stack or disable the flag |
| `DeepSpeed config is required for DMD distillation` | DMD + DeepSpeed path lacks generator/critic config | Provide both configs or use the non-DeepSpeed path |
| `efficient_sample requires pyramid_sample_mode='full'` | Efficient sampling was enabled with a non-full pyramid sampler | Switch to `pyramid_sample_mode: full` or disable efficient sampling |
| Clean patch embedding assertion fails | Multi-term memory patch or zero-history options lack the required stage-1 flags | Enable `has_multi_term_memory_patch` and `is_enable_stage1`, or turn off those options |
| Error-recycling conflict assertion | `use_error_recycling` was combined with history/model-input corruption | Keep only one corruption/recycling path for a run |
| Reward model assertion | Reward-model training has no positive VQ/MQ reward weight | Set a positive reward weight or disable the reward model |
| GAN assertion | GAN training lacks DMD or lacks both GAN hook/final paths | Enable DMD and at least one GAN hook/final option |
| Stage-3 dataset has no GAN/ODE/text roots | The selected stage-3 variant has no data source | Fill the matching `gan_data_root`, `ode_data_root`, or `text_data_root` |

## Preflight habit

Run the validation helper after every config edit. It catches the highest-value
invariants without loading checkpoints or starting a distributed job.
