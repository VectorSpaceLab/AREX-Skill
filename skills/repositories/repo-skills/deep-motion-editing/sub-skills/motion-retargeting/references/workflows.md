# Retargeting workflows

Run the source repository's commands with the current working directory set to
its `retargeting/` directory. Relative paths in the source code are resolved
there: `option_parser.get_std_bvh()` looks for
`./datasets/Mixamo/std_bvhs/<character>.bvh`, and dataset loaders look for
`./datasets/Mixamo/mean_var`, `.npy` character files, and the list files.
The bundled scripts accept a user-supplied checkout and preserve this working
-directory convention without embedding any checkout path.

## Preflight a pair

```bash
python skills/disco/deep-motion-editing/sub-skills/motion-retargeting/scripts/validate_retargeting_data.py \
  --pair "datasets/Mixamo/Aj/Dancing Running Man.bvh" \
        "datasets/Mixamo/BigVegas/Dancing Running Man.bvh"
```

The validator reports hierarchy-level facts, not neural compatibility. A pair
can parse successfully and still fail because `BVH_file` cannot classify its
skeleton or because the standard BVH, end-effectors, simplified topology, and
normalization statistics do not agree.

## Single-pair inference

The unmodified entry point is:

```bash
cd <user-checkout>/retargeting
python eval_single_pair.py \
  --input_bvh datasets/Mixamo/Aj/Dancing_Running_Man.bvh \
  --target_bvh datasets/Mixamo/BigVegas/Dancing_Running_Man.bvh \
  --test_type intra \
  --output_filename examples/intra_structure/result.bvh \
  --save_dir ./pretrained --cuda_device cuda:0 --eval_seq 0
```

The arguments containing spaces are deliberately passed with underscores in
this example because `recover_space()` in `eval_single_pair.py` converts every
underscore to a space. This is a legacy workaround, not a general escaping
rule. It also changes underscores in directory names and output names. A
literal underscore is therefore unsafe with the unmodified script. Use
`run_retargeting.py` to see a safe command and an actionable rejection, or
patch the upstream recovery function and select `--path-mode literal` only
after testing that patch.

Safe dry-run construction (no model import or execution):

```bash
python .../run_retargeting.py \
  --repo-root <user-checkout> \
  --input-bvh "<user-checkout>/retargeting/datasets/Mixamo/Aj/Dancing Running Man.bvh" \
  --target-bvh "<user-checkout>/retargeting/datasets/Mixamo/BigVegas/Dancing Running Man.bvh" \
  --output-filename "<user-checkout>/retargeting/examples/intra result.bvh" \
  --test-type intra --save-dir ./pretrained
```

Add `--run` only after the checkpoint preflight passes and the requested
backend is available. The helper accepts `--cuda-device cpu`; source code also
falls back to CPU when CUDA is not available. CUDA is recommended for a real
model run. The output parent is created only in `--run` mode.

### Intra versus cross

`eval_prepare()` derives character names from the parent directories of the
input and target paths. For `intra`, an input character ending in `_m` is
paired with `BigVegas`; otherwise the source is paired with `Goblin_m`. For
`cross`, each side is a one-character group, with the input motion placed in
the source group and a standard target entry in the opposite group. This
means directory names are semantically used; do not flatten the files into a
single directory. `eval_seq` is used by the standard evaluation character
permutation, while a single-pair input path supplies the actual motion.

## Demo and batch evaluation

README's demo workflow is simply `cd retargeting && sh demo.sh`; source
`demo.py` runs two hard-coded examples (`intra` and `cross`), writes example
copies, invokes `eval_single_pair.py`, then runs `models.IK.fix_foot_contact`.
Prefer the helper's command construction when adapting this to new files:

```bash
python .../run_retargeting.py --repo-root <user-checkout> \
  --workflow demo --save-dir ./pretrained
python .../run_retargeting.py --repo-root <user-checkout> \
  --workflow eval --save-dir ./pretrained --eval-seq 0 --cuda-device cuda:0
```

`eval.py` loads the first line of `save_dir/para.txt`, reparses its training
arguments, forces evaluation/quaternions, and calls `model.load(epoch=20000)`.
It writes generated BVHs below `save_dir/results/bvh/<character>/` with
`<id>_<source>.bvh` and `<id>_gt.bvh`. `test.py` loops over four test
characters and evaluation sequences, computes errors through `get_error.py`,
copies aggregate files into `results/cross_structure` and
`results/intra_structure`, prints mean errors, and removes `results/bvh`.
That launcher is data-dependent and potentially destructive; the bundled
helper refuses to execute it unless `--allow-destructive-test` is supplied.

## Training

After Mixamo/custom preparation:

```bash
cd <user-checkout>/retargeting
python train.py --save_dir ./training/ --cuda_device cuda:0
```

The training wrapper defaults to dry-run and exposes the important parser
values:

```bash
python .../run_training.py --repo-root <user-checkout> \
  --dataset-root <user-checkout>/retargeting/datasets/Mixamo \
  --save-dir ./training --window-size 64 --rotation quaternion \
  --batch-size 256 --epoch-num 20001 --learning-rate 2e-4 \
  --num-layers 2 --cuda-device cuda:0
```

Pass repeated `--extra-arg=--verbose=1` or another source parser option only
when its spelling has been checked. `train.py` writes `save_dir/para.txt`,
logs, `models/topology0` and `models/topology1`, and periodic epoch
checkpoints. Training data is unpaired across the two hard-coded character
groups; the model uses mixed datasets and random target skeleton instances.
