# ESPnet2 Configuration and Components

ESPnet2 YAML configs mirror command-line options. This means the following forms are equivalent when the module accepts `foo` and `bar`:

```yaml
foo: 3
bar: 4
```

```bash
python -m espnet2.bin.asr_train --config config.yaml
python -m espnet2.bin.asr_train --foo 3 --bar 4
```

## Nested `*_conf` values

Parameters named `*_conf` accept repeated key-value entries or YAML-like strings:

```bash
python -m espnet2.bin.asr_train --optim_conf lr=0.001 --optim_conf weight_decay=0
python -m espnet2.bin.asr_train --optim_conf "{lr: 0.001, weight_decay: 0}"
```

Use `--print_config` after selecting a class choice to see nested defaults:

```bash
python -m espnet2.bin.asr_train --encoder conformer --print_config
python -m espnet2.bin.asr_train --scheduler warmuplr --print_config
```

## Component selection surfaces

Typical task configs include choices for frontend, specaug, normalize, encoder, decoder, CTC, model, optimizer, scheduler, tokenization, losses, and data iterator/batching. Component-specific imports may require optional dependencies such as S3PRL, Whisper, k2, Longformer, FlashAttention, pyworld, or G2P packages.

Troubleshooting rule: install the dependency required by the selected component/config, not a broad extra group, unless the user's workflow genuinely spans many optional families.
