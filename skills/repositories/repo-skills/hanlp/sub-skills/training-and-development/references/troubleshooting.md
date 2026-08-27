# Training and Development Troubleshooting

- Unexpected downloads: training demos can fetch datasets, pretrained transformers, and HanLP resources. Set cache paths and confirm internet/offline assets before running.
- `save_dir` problems: keep model outputs separate from source files and remove stale configs between incompatible experiments.
- OOM/device issues: lower `batch_size`, use gradient accumulation, smaller models, or a verified GPU-enabled backend.
- Optional dependency problems: TensorFlow classifier paths need `hanlp[tf]`; AMR paths need `hanlp[amr]`; broad `full` installs can destabilize an environment.
- Test failures: separate deterministic local tests from network/model-cache/service-dependent tests before debugging source behavior.
