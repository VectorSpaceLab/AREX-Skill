# trlX training troubleshooting

Use this matrix for training/config/sweep failures in the Accelerate-backed trlX stack. For NeMo/Megatron/Apex-specific errors, route to `../nemo/SKILL.md`.

## Install and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: trlx` | trlX is not installed in the active Python environment | Install trlX into the environment that will run training; verify with `python -c "import trlx; print(trlx.__version__)"` or the root install-check helper when integrated. |
| Package imports under one shell but not under `accelerate launch` | Different Python executable/environment for launcher workers | Run `which python`, `python -m pip show trlx`, and `accelerate env`; launch with the intended environment activated for every worker. |
| Python version incompatibility | trlX 0.7.0-era dependencies were verified on Python 3.10 and documented for Python 3.9-3.11 | Use a 3.9-3.11 environment for training. Avoid bleeding-edge Python for this package. |
| `pip check` reports packaging/wheel/setuptools conflicts | Pinned 2023 dependencies can conflict with newer packaging stack | Prefer a fresh environment. If Ray or wheel tooling fails, pin compatible `setuptools` and `wheel` versions for the training environment. |
| NeMo trainer import raises that NeMo is not installed | The normal inspection environment registers dummy NeMo trainers when NeMo/Apex is absent | Do not use NeMo trainers from this sub-skill. Route to the NeMo sub-skill and prepare a separate NeMo/Apex environment. |

## Ray Tune and `pkg_resources`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: pkg_resources` while importing or running Ray | Newer setuptools no longer exposes `pkg_resources` the way Ray 2.x expects | Install a setuptools release that still provides `pkg_resources`, for example `python -m pip install 'setuptools<70'`, then rerun `python -m pip check`. |
| Sweep starts but imports training script too early | `python -m trlx.sweep` imports the script module before launching trials | Keep dataset downloads, model loading, and `trlx.train` calls inside `main(hparams={})`; top level should define config/data helpers only. |
| Sweep asks for confirmation and blocks automation | CLI safety prompt | Pass `-y`/`--assume_yes` only after reviewing top-level side effects and resource use. |
| W&B report creation fails after sweep | W&B credentials/project/entity unavailable | Disable report-dependent automation for unattended runs or configure W&B before launching the sweep. |

## W&B, TensorBoard, and logging

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training hangs or errors waiting for W&B login | `config.train.tracker` defaults to `"wandb"` in many configs | Set `config.train.tracker = None` for local smoke tests, or set `WANDB_MODE=disabled`/offline credentials as appropriate. |
| TensorBoard config serialization fails with PEFT config | PEFT config objects are not naturally TensorBoard-hparam serializable | Use dict PEFT configs when possible; trlX stringifies PEFT config for TensorBoard, but complex objects can still be awkward. |
| Console output too noisy | Progress bars and third-party logs | Use `trlx.logging.disable_progress_bar()`, set `TRLX_VERBOSITY=WARNING`, and lower `transformers` logging in the user script. |

## CUDA, Accelerate, and DeepSpeed

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `torch.cuda.is_available()` false | CPU PyTorch wheel, unavailable GPU, or launcher not exposing GPUs | Install a CUDA-capable PyTorch wheel matching the host driver; check `CUDA_VISIBLE_DEVICES`; verify outside trlX before launching. |
| CUDA out of memory during rollout generation | `seq_length`, `max_new_tokens`, `batch_size`, PPO `chunk_size`, or model size too high | Lower `train.batch_size`, set `train.minibatch_size`, lower `method.chunk_size`, reduce `seq_length`/`max_new_tokens`, freeze layers, enable PEFT, or use DeepSpeed. |
| DeepSpeed fp16 type/cast errors | Mixed precision or ZeRO config mismatch | Try bf16 on A100-class GPUs; use a known-good Accelerate YAML; trlX disables DeepSpeed fp16 auto-cast of forward inputs, but dependency version mismatches can still surface. |
| Distributed launch deadlocks | Wrong rank/world-size environment or inconsistent visible GPUs | Confirm `accelerate config`, `num_processes`, node ranks, `MASTER_ADDR`, and `MASTER_PORT`; avoid mixing scheduler launchers with `accelerate launch` defaults unless configured deliberately. |
| ZeRO-3 save/load surprises | Sharded state and consolidated model save expectations | Include `zero3_save_16bit_model: true` when a consolidated 16-bit model is needed; always test `trainer.save_pretrained` and `resume_from_checkpoint` on a small run first. |

## Hugging Face downloads, datasets, and cache

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training stalls before model init | Model/tokenizer/dataset download | Pre-populate cache, use local model/data paths, or set `HF_HOME`/`TRANSFORMERS_CACHE`/dataset cache env vars for the job. |
| Offline cluster cannot resolve model names | Hub access unavailable | Use local directories for `model.model_path` and `tokenizer.tokenizer_path`; avoid source examples that implicitly call `load_dataset` or `pipeline` at top level. |
| Reward function imports a large classifier on every worker | Pipeline/model constructed per process | Build reward models deliberately, use `LOCAL_RANK` to select device, and avoid top-level loads in sweep scripts. |
| Dataset examples too slow or credentialed | Public examples often download datasets/models or use W&B/Triton | Reduce to a small slice or synthetic fixture for validation; do not run full example-family workflows unless the user approved time/network/GPU use. |

## Tokenizer and prompt/data shape errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'max_new_tokens'` | `config.method.gen_kwargs` lacks `max_new_tokens` | Add `max_new_tokens` to method generation kwargs. Some YAMLs use `max_length` for other purposes, but `trlx.train` expects `max_new_tokens`. |
| Negative or tiny prompt budget | `seq_length <= max_new_tokens` | Increase `train.seq_length` or reduce `method.gen_kwargs.max_new_tokens`. |
| `ValueError: Either samples or reward_fn should be given for training` | Missing mode-defining arguments | Use `reward_fn` for PPO/RFT online, or `samples` for ILQL/SFT offline. |
| `Number of samples ... should match the number of rewards` | Offline ILQL length mismatch | Ensure one scalar reward per sample. |
| `Dialogue must have an even number of phrases` | Dialogue sample list is not alternating prompt/output pairs | Use `[prompt, output]` or `[prompt1, output1, prompt2, output2]`. |
| Prompt metadata missing in reward function | Prompt dict lacked `"prompt"` key or function signature did not accept metadata | Use dicts like `{"prompt": text, "reference": ref}` and include `**metadata` or named metadata args in `reward_fn`/`metric_fn`. |
| Original prompt dicts lose `"prompt"` after pipeline construction | `PromptPipeline` pops `"prompt"` from dicts while storing metadata | Pass copies if those dicts are needed later. |
| Padding token errors with GPT-style tokenizers | Tokenizer lacks native pad token or model embeddings do not match added special token | Set tokenizer/model consistently. If adding new special tokens in a custom script, resize embeddings before training; otherwise consider using EOS as pad if compatible. |
| Unexpected truncation direction | `tokenizer.truncation_side` controls `PromptPipeline` and `tokenize_dialogue` | Set `truncation_side` explicitly; use right truncation for many causal examples and right padding/truncation for T5 examples unless the task requires otherwise. |

## PEFT and 8-bit limitations

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: peft` | `model.peft_config` set but PEFT package missing | Install `peft` in the training environment or remove `peft_config`. |
| `num_layers_unfrozen` appears ignored | PEFT is active | This is expected; trlX warns and ignores `num_layers_unfrozen` under PEFT. Use PEFT adapter settings such as LoRA target modules/modules-to-save instead. |
| `load_in_8bit` raises `NotImplementedError` | trlX `PreTrainedModelWrapper` rejects 8-bit model loading | Do not use `load_in_8bit` with PPO/ILQL wrappers. Bitsandbytes optimizer names are separate and may still work if bitsandbytes is installed. |
| `adamw_8bit_bnb` import error | bitsandbytes missing or incompatible with platform/CUDA | Install a compatible bitsandbytes build, or switch optimizer `name` to `adamw`. |
| PEFT seq2seq prompt/prefix behavior is odd | Prefix/prompt tuning adds virtual tokens and requires bypass logic | Prefer LoRA for seq2seq. Validate generation and save/load on a small model before a full run. |
| Loaded PEFT checkpoint missing base weights | PEFT checkpoint stores adapter plus trlX heads, not a full base model | Load with the same or accessible base model path recorded in the adapter config; keep extra head `pytorch_model.bin` with the adapter files. |

## Checkpoint and resume failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Resume silently starts fresh | `config.train.resume_from_checkpoint` path does not exist | Verify the checkpoint directory before calling `trlx.train`. trlX only loads when the path exists. |
| Missing `best_checkpoint` | `save_best=False`, no reward/metric improvement, or evaluation never ran | Set `save_best=True`, set `eval_interval` below `total_steps`, and ensure reward/metric keys are produced. |
| Disk fills during training | Frequent full checkpoints or sweep trials | Increase `checkpoint_interval`, set `save_best=False` for sweeps, set `save_optimizer=False` when resumability is unnecessary, or clean old trial directories. |
| PEFT checkpoint has unexpected file sizes | Adapter/head-only behavior | For PPO/ILQL PEFT, compact `pytorch_model.bin` should hold value/ILQL heads; adapter files hold PEFT weights. Large full-model bins indicate a non-PEFT or mis-saved path. |
| `trainer.save_pretrained` output cannot be loaded for inference | Wrong model wrapper or missing tokenizer/base model | Save via the trainer, keep tokenizer files, keep adapter/head files together, and load with the corresponding trlX wrapper when value/ILQL heads are needed. |

## Seq2seq and SFT limitations

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Seq2seq SFT fails or loads wrong architecture | `AccelerateSFTTrainer` uses `AutoModelForCausalLM` | Use causal SFT, or implement a custom seq2seq SFT trainer outside stock trlX 0.7.0. PPO/ILQL support seq2seq wrappers. |
| RFT with T5/seq2seq fails | `AccelerateRFTTrainer` uses `AutoModelForCausalLM` | Treat RFT as causal-only unless extending trainer code. |
| `Value branches unsupported for Seq2Seq architecture` | `num_value_layers_unfrozen > 0` with seq2seq value head | Keep `num_value_layers_unfrozen=0` for seq2seq PPO. |
| T5 output/reward function receives unexpected strings | Seq2seq decoding uses decoder output and may combine prompt/output with separator for samples | Write reward/metric functions against `outputs` for target text and `prompts` for source text; avoid parsing combined `samples` unless necessary. |

## Safe debugging sequence

1. Run the bundled config inspector on the default/YAML config.
2. Disable W&B and use a tiny model or local cached model.
3. Use two to eight samples/prompts, `total_steps=1`, low `batch_size`, and low `max_new_tokens`.
4. Confirm reward/metric callbacks receive the expected `samples`, `prompts`, `outputs`, and metadata.
5. Add Accelerate/DeepSpeed only after a single-process smoke works.
6. Add PEFT or sweeps only after base config/data shapes are stable.
