# Retargeting API and configuration reference

These facts are distilled from `retargeting/option_parser.py`,
`eval_single_pair.py`, `eval.py`, `train.py`, `datasets/__init__.py`,
`datasets/combined_motion.py`, `datasets/motion_dataset.py`,
`datasets/bvh_parser.py`, `datasets/bvh_writer.py`, and the model modules.
The original checkout is evidence, not a runtime dependency of this skill.

## CLI parser

`option_parser.get_parser()` returns an `argparse.ArgumentParser`. Important
verified defaults are:

| argument | default | role |
|---|---:|---|
| `--save_dir` | `./pretrained` | save/log/checkpoint/result root |
| `--cuda_device` | `cuda:0` | requested torch device |
| `--window_size` | `64` | time axis per training window |
| `--rotation` | `quaternion` | raw input representation; eval forces this |
| `--dataset` | `Mixamo` | parser dataset label |
| `--eval_seq` | `0` | evaluation character-sequence index |
| `--num_layers` | `2` | encoder/decoder hierarchy depth |
| `--batch_size` | `256` | training batch size |
| `--epoch_num` | `20001` | training loop upper bound |
| `--learning_rate` | `2e-4` | Adam learning rate |
| `--normalization` | `1` | mean/std normalization enabled |
| `--model` | `mul_top_mul_ske` | only implemented model selector |
| `--pos_repr` | `3d` | root position representation |
| `--fk_world` | `0` | forward-kinematics world/local option |
| `--gan_mode` | `lsgan` | discriminator loss mode |
| `--ee_velo` | `1` | end-effector velocity feature |
| `--ee_from_root` | `1` | end-effector root-relative feature |
| `--is_train` | `1` | training versus evaluation mode |

Other parser defaults include `kernel_size=15`, `upsampling=linear`,
`downsampling=stride2`, `batch_normalization=0`, `activation=LeakyReLU`,
`data_augment=1`, `padding_mode=reflection`, `skeleton_dist=2`,
`skeleton_pool=mean`, `patch_gan=1`, `skeleton_info=concat`,
`lambda_rec=5`, `lambda_cycle=5`, `lambda_ee=100`,
`lambda_global_pose=2.5`, `lambda_position=1`, `scheduler=none`, and
`rec_loss_mode=extra_global_pos`.

`eval_single_pair.py` adds four required arguments: `--input_bvh`,
`--target_bvh`, `--test_type`, and `--output_filename`. It parses the common
options first, recovers spaces, reads `save_dir/para.txt`, reparses the stored
training arguments, then overrides `cuda_device`, `is_train=False`,
`rotation=quaternion`, and `eval_seq`. It loads epoch `20000` (hard-coded),
not the newest available epoch. Its initial `--save_dir` is used to locate
`para.txt`, but after reading that file the source replaces the entire args
object with the recorded command-line args. Consequently the recorded
`--save_dir` must resolve to the same checkpoint root when single-pair
inference reaches `BaseModel`; passing a different lookup directory alone does
not relocate the run. `eval.py` differs: it explicitly restores `args.save_dir`
after reading `para.txt`.

## Dataset objects and signatures

- `datasets.create_dataset(args, character_names)` selects `MixedData` when
  `args.is_train` is truthy and `TestData` otherwise.
- `datasets.get_character_names(args)` returns training groups
  `[['Aj', 'BigVegas', 'Kaya', 'SportyGranny'], [20 male-character names]]`.
  In eval it returns four repeated `BigVegas` entries and four male test
  characters, swapping the sequence selected by `args.eval_seq` into slot 0.
  Custom character sets require editing the source `datasets/__init__.py` and
  matching standard/statistics files; a CLI dataset name does not override
  these hard-coded lists.
- `MotionData(args)` loads `./datasets/Mixamo/<args.dataset>.npy`, subsamples
  every second frame, clips overlapping windows of size `args.window_size`
  (step is half the window), converts Euler rotations to quaternions, and
  computes mean/std. A zero or tiny std is replaced by one.
- `TestData.get_item(gid, pid, id)` accepts either an integer test-list index
  or a string path, parses with `BVH_file`, converts to quaternion when
  requested, subsamples every second frame, and truncates to a length divisible
  by four. It needs per-character `mean_var/*.npy` and `std_bvhs/*.bvh`.

## BVH parser and writer facts

`datasets.bvh_parser.BVH_file(file_path=None, args=None, dataset=None,
new_root=None)` classifies a file against hard-coded joint-name lists. It
exposes `anim`, original `_names`, `frametime`, `topology`, `edges`, `names`,
`offset`, `get_ee_id()`, `get_height()`, `get_ee_length()`,
`to_numpy(quater=False, edge=True)`, `to_tensor(quater=False, edge=True)`,
and `write(file_path)`. It removes namespace prefixes before classification.
Skeleton type 0 is re-rooted at joint 1; type 3 is preferred for complete CMU
names; special names select split-arm and other types.

`datasets.bvh_writer.BVH_writer(edges, names)` writes `write(rotations,
positions, order, path, frametime=1/30, offset=None, root_y=None)` or
`write_raw(motion, order, path, frametime=1/30, root_y=None)`. Quaternion
rotation tensors are normalized and converted to XYZ Euler channels for BVH.
The output writer includes virtual joints where topology edges require them.

## Model and kinematics route

`models.create_model(args, character_names, dataset)` supports only
`args.model == 'mul_top_mul_ske'` and creates `models.architecture.GAN_model`.
Each topology has an `IntegratedModel` containing an auto-encoder, static
encoder, discriminator, and `ForwardKinematics` object. During inference,
the source latent is decoded with the destination topology's static offset
representation. `ForwardKinematics.forward_from_raw(raw, offset, world=None,
quater=None)` expects raw tensors with time last and returns global positions;
quaternion inputs have four channels, while the unsupported `pos_repr=4d`
path raises an exception. The model normalizes quaternions before converting to
rotation matrices.

Training's `GAN_model.forward()` reconstructs each group and performs all
source/destination combinations. Losses include reconstruction, cycle,
end-effector, position, and optional least-squares GAN terms. This is why
training is much more expensive than a parser check and why matching topology,
window size, normalization, and standard offsets is essential.

## Checkpoint and result contract

For the hard-coded epoch-20000 pretrained loader, `save_dir` must contain:

```text
save_dir/
  para.txt
  models/
    topology0/20000/auto_encoder.pt
    topology0/20000/static_encoder.pt
    topology1/20000/auto_encoder.pt
    topology1/20000/static_encoder.pt
```

`IntegratedModel.save()` may also write `height.pt` and discriminator weights;
the inference loader explicitly requires the auto-encoder and static-encoder
files. `para.txt` is the first-line command captured by `train.py` and must
contain arguments that reproduce the model's architecture and a usable
`--save_dir`. A missing file, wrong epoch, malformed command line, stale
relative save path, or incompatible tensor shapes fails late at model
construction/loading; preflight it early.

Single-pair output is copied from the model's temporary
`save_dir/results/bvh/<target-character>/0_<source-id>.bvh` to the requested
filename. Batch output is `<id>_<source>.bvh` plus `<id>_gt.bvh` under the same
result tree. The source demo's `fix_foot_contact` assumes foot joint names
`RightToeBase`, `LeftToeBase`, `LeftFoot`, and `RightFoot`; it is not a generic
cleanup operation for arbitrary custom skeletons.
