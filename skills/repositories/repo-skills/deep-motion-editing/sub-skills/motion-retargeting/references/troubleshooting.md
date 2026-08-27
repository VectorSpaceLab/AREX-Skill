# Retargeting troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `cannot find ... eval_single_pair.py` | helper received the wrong checkout/root | Pass a user checkout containing `retargeting/`, or pass that directory itself. The helper does not infer a private source path. |
| `BVH_file` prints names then raises `Unknown skeleton` | joint names do not match a hard-coded `corps_names` entry | Inspect names and hierarchy; use a supported Mixamo/CMU-style skeleton or extend the source parser's lists and end-effectors. A generic BVH passing the standalone validator is not enough. |
| `Problem in file` or incorrect topology | required joints are missing, duplicated, or ordered unexpectedly | Compare the standard BVH and motion BVH; preserve a common T-pose and names. Do not delete joints after preprocessing without updating the hard-coded skeleton definition. |
| `Cannot find file`, missing `mean_var`, or missing `std_bvhs` | preprocessing did not finish or paths are being resolved from the wrong cwd | Run from `retargeting`; validate `datasets/Mixamo`, then run the user-controlled preprocessing sequence. |
| `path contains '_' and cannot survive ... recovery` | legacy `recover_space()` turns every underscore into a space | Rename the file/directory to remove underscores, encode spaces as underscores, or patch upstream recovery and use literal mode only after testing. There is no safe escape for a literal underscore in the original script. |
| source path with spaces is not found | command was passed to a shell unquoted or space encoding was omitted | Use the bundled runner (argv, not shell) and its default encoding. Check the printed command; it should show spaces as `_` for the unmodified single-pair script. |
| `Unknown test type` | spelling/case is not exactly `intra` or `cross` | Use one of the two exact choices. `intra` uses fixed same-structure companion characters; `cross` uses separate one-character groups. |
| inference rejects a tensor shape | `para.txt` was made with different `rotation`, `window_size`, `num_layers`, topology, or normalization settings | Preserve `para.txt` from the checkpoint run and inspect the saved arguments. Evaluation forces quaternion mode but still depends on compatible other architecture settings. |
| `FileNotFoundError: save_dir/para.txt` | save directory points at a run root without its training record | Set `--save-dir` to the directory containing `para.txt`, not merely the checkpoint parent. |
| model load fails under `models/topology0` or `topology1` | incomplete checkpoint tree, wrong epoch, or incompatible PyTorch state dict | Supply both topology 0/1 auto-encoder and static-encoder files at `20000`; check exact architecture options. The loader does not download or choose an arbitrary latest epoch in single-pair evaluation. |
| CUDA error, unavailable device, or occupied GPU | default is `cuda:0`, but machine/runtime does not have a usable CUDA device | Pass `--cuda-device cpu`; evaluation also falls back to CPU if `torch.cuda.is_available()` is false. CPU is slower and is not a substitute for a full performance claim. Retry with an explicitly available CUDA device after checking the environment. |
| `ModuleNotFoundError: models` or `datasets` | source scripts depend on cwd/sys.path | Run from the user's `retargeting/` directory or let the wrapper set `cwd`. Do not install this skill as if it were the original Python package. |
| `RuntimeError` while importing legacy NumPy utility | old `utils` code can rely on removed internal NumPy extensions | Read the shared [`animation-data`](../../animation-data/SKILL.md) import caveat; use the standalone validator for format checks and a deliberately pinned inspection environment for legacy model execution. |
| `demo.py` fails in foot cleanup | output skeleton lacks one of `RightToeBase`, `LeftToeBase`, `LeftFoot`, `RightFoot` | Treat foot cleanup as optional and skeleton-specific; validate raw output first. Route general BVH/output handling to [`animation-data`](../../animation-data/SKILL.md). |
| output file exists but validator rejects it | upstream copied a partial/malformed file or target writer encountered incompatible topology | Keep the source result staging tree, inspect stdout and checkpoint compatibility, and rerun with a distinct output path. Do not overwrite the only source motion. |
| batch test destroys evidence | `test.py` removes `save_dir/results/bvh` after collecting errors | Use the wrapper's dry run first; back up or copy results, then explicitly add `--allow-destructive-test`. |
| training never progresses or exhausts memory | source defaults are large: batch 256, 20,001 epochs, two topology groups, GAN losses | Lower batch size/window or run a small configuration only as a smoke test; do not interpret it as a paper result. CUDA is recommended. |
| `preprocess.py` fails while copying first file | empty character directory or shell/path issue | Ensure each character has at least one `.bvh`, avoid relying on spaces in the source shell command, and make `std_bvhs`/`mean_var` writable. Use the validator before retrying. |
| FBX conversion fails | Blender is missing or source script's bulk path assumptions are wrong | Use the Blender sibling route and its explicit command builder; inspect FBX imports and output one file at a time. Do not auto-download FBX or Blender. |

## Verify an output without the model

The standalone validator checks frame rows, channel counts, positive frame
interval, and hierarchy basics:

```bash
python .../validate_retargeting_data.py --bvh output.bvh --json
```

It does not run forward kinematics or compare positions. For a semantic
comparison, parse both source and target/output with a compatible BVH utility,
confirm frame count and target joint order, and compare normalized global
end-effector positions. The source `get_error.py` computes mean squared global
position error against a target standard motion, normalized by target height,
but its batch launcher depends on the fixed test tree and uses shell commands;
use it as a reference, not as a bundled safe helper.

## Runtime boundary

`download_test.sh`, `fbx2bvh.py`, `split_joint.py`, `preprocess.py`, `test.py`,
`eval.py`, `get_error.py`, and `demo.py` remain source-artifact decisions:
this skill documents their contracts and wraps only safe, user-selected
commands. The bundled scripts contain no checkpoints, no download URL, no
training implementation, and no production checkout path.
