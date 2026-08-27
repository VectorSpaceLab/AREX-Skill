# Training CLI

`train/train.py` parses these important options before building the graph:

| Option | Default | Meaning |
|---|---:|---|
| `--gpu` | `0` | TensorFlow GPU index |
| `--model` | `frustum_pointnets_v1` | importable model module |
| `--log_dir` | `log` | checkpoint and summary directory |
| `--num_point` | `2048` | sampled points per frustum |
| `--max_epoch` | `201` | epoch count |
| `--batch_size` | `32` | training batch |
| `--learning_rate` | `0.001` | initial rate |
| `--momentum` | `0.9` | momentum optimizer parameter |
| `--optimizer` | `adam` | `adam` or `momentum` |
| `--decay_step` | `200000` | learning-rate/BN decay step |
| `--decay_rate` | `0.7` | decay factor |
| `--no_intensity` | false | use XYZ (3 channels) instead of XYZ+intensity (4) |
| `--restore_model_path` | none | TensorFlow checkpoint prefix |

The shell templates use smaller point counts and altered decay settings for
their v1/v2 variants. Prefer explicit flags over relying on those templates.
The model name must match an available model module and its checkpoint must
have compatible variable names.
