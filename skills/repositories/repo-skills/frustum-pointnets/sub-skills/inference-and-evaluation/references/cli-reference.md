# Test CLI

`train/test.py` accepts:

| Option | Default | Purpose |
|---|---|---|
| `--gpu` | `0` | TensorFlow device index |
| `--num_point` | `1024` | points per frustum |
| `--model` | `frustum_pointnets_v1` | model module/checkpoint family |
| `--model_path` | `log/model.ckpt` | checkpoint prefix |
| `--batch_size` | `32` | inference batch |
| `--output` | `test_results` | output pickle/result stem |
| `--data_path` | none | alternate frustum pickle |
| `--from_rgb_detection` | false | use detector-frustum schema |
| `--idx_path` | none | frame ids for RGB result files |
| `--dump_result` | false | also serialize predictions |

The source test script creates a graph, restores the checkpoint, predicts masks,
centers, heading/size classes and residuals, then writes KITTI label rows. Keep
`--num_point`, model, input channels, and checkpoint architecture aligned.
