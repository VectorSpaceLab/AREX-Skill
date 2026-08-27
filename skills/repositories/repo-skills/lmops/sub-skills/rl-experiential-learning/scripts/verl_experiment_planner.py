"""Safe planner for LMOps VeRL/Ray/vLLM experiential-learning workflows.

This script prints command skeletons and prerequisite checklists only. It never
starts Docker, Ray, vLLM, training, evaluation, checkpoint merging, downloads,
W&B, Hugging Face, OpenAI-compatible calls, or IF-Eval.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence


COACH_ALIASES: Dict[str, Dict[str, str]] = {
    "qwen-el-self": {"mode": "el", "long": "wildchat-el-q3-8b-r8b", "feedback": "self"},
    "qwen-el-self-iter": {"mode": "el", "long": "wildchat-el-q3-8b-r8b-itert30-mopd025-fixt", "feedback": "self-iter"},
    "qwen-el-gpt4o": {"mode": "el", "long": "wildchat-el-q3-8b-rgpt4o", "feedback": "openai"},
    "olmo-el-self": {"mode": "el", "long": "wildchat-el-om3-7b-r7b", "feedback": "self"},
    "olmo-el-gpt4o": {"mode": "el", "long": "wildchat-el-om3-7b-rgpt4o", "feedback": "openai"},
    "qwen-rl-self": {"mode": "rl", "long": "wildchat-rl-q3-8b-r8b", "feedback": "self"},
    "qwen-rl-gpt4o": {"mode": "rl", "long": "wildchat-rl-q3-8b-rgpt4o", "feedback": "openai"},
    "olmo-rl-self": {"mode": "rl", "long": "wildchat-rl-om3-7b-r7b", "feedback": "self"},
    "olmo-rl-gpt4o": {"mode": "rl", "long": "wildchat-rl-om3-7b-rgpt4o", "feedback": "openai"},
}


@dataclass
class Plan:
    title: str
    summary: str
    prerequisites: List[str] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "title": self.title,
            "summary": self.summary,
            "prerequisites": self.prerequisites,
            "validations": self.validations,
            "commands": self.commands,
            "warnings": self.warnings,
            "notes": self.notes,
            "safe": True,
        }


def q(value: object) -> str:
    return shlex.quote(str(value))


def placeholder(value: object | None, token: str) -> str:
    if value is None or value == "":
        return f"<{token}>"
    return str(value)


def parse_credentials(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def credential_notes(creds: Iterable[str]) -> List[str]:
    out: List[str] = []
    wanted = set(creds)
    if "wandb" in wanted:
        out.append("Confirm W&B project/API-key environment variables on the target host; do not embed secret values in commands.")
    if "hf" in wanted or "huggingface" in wanted:
        out.append("Confirm Hugging Face token/cache access for gated models or datasets before execution.")
    if "openai" in wanted or "gpt4o" in wanted:
        out.append("Confirm OpenAI-compatible API key and optional base URL/model variables before coach or scoring calls.")
    return out


def common_prereqs(args: argparse.Namespace) -> List[str]:
    bits = [
        "Prepared target checkout and environment; this planner does not run setup.",
        f"GPU topology resolved: nodes={args.nodes}, gpus_per_node={args.gpus_per_node}, gpu_class={args.gpu_class}.",
        "Ray/vLLM readiness confirmed outside this script before any real trainer command.",
    ]
    if args.gpu_class == "b200":
        bits.append("Use the B200-specific setup path in the target checkout; do not mix it with A100/H100/H200 setup artifacts.")
    elif args.gpu_class in {"a100", "h100", "h200"}:
        bits.append("Use the A100/H100/H200 setup path in the target checkout.")
    return bits + credential_notes(parse_credentials(args.credentials))


def plan_oel(args: argparse.Namespace) -> Plan:
    stage = args.stage or "round"
    model = placeholder(args.model, "MODEL_OR_ID")
    exp = placeholder(args.exp_name, "EXP_NAME")
    textgame = args.textgame_name or "Sokoban-v0"
    steps = args.textgame_max_steps
    no_think = str(args.textgame_no_think).lower()
    exp_len = args.experience_max_length
    resp_len = args.max_response_length
    round_id = args.round
    ckpt_start = placeholder(args.checkpoint_start, "CKPT_START")
    ckpt_end = placeholder(args.checkpoint_end, "CKPT_END")
    ckpt_step = placeholder(args.checkpoint_step, "CKPT_STEP")
    val_limit = args.val_samples_limit
    val_use = args.val_samples_use
    prompt_version = args.prompt_version
    commands: List[str] = []

    extract_exp = f"{exp}-extract-round{round_id}"
    deploy_exp = f"{exp}-deploy-round{round_id}"
    consolidate_exp = f"{exp}-round{round_id}"

    if stage in {"round", "all", "extract"}:
        config = ",".join([
            extract_exp,
            str(ckpt_start),
            str(ckpt_end),
            str(ckpt_step),
            model,
            placeholder(args.resume_checkpoint, "RESUME_CKPT"),
            prompt_version,
            str(val_limit),
            str(args.exp_sel_with_prev).lower(),
            str(exp_len),
            textgame,
            str(args.textgame_response_length),
            str(steps),
            no_think,
            str(round_id),
            placeholder(args.exp_model, "EXP_MODEL_OPTIONAL"),
        ])
        commands.append(f"bash scripts/textgame_extract_inturn.sh {q(config)}")
        commands.append(
            "python tools/make_exp_list.py "
            + q(",".join([extract_exp, str(ckpt_start), str(ckpt_end), str(ckpt_step), str(val_limit), str(val_use)]))
        )
    if stage in {"round", "all", "deploy"}:
        commands.append(
            "bash scripts/textgame_generate_deploy.sh "
            f"--model {q(model)} --exp_name {q(deploy_exp)} --nnodes {args.nodes} --oel_round {round_id} "
            f"--experience_max_length {exp_len} --textgame_name {q(textgame)} --max_response_length {resp_len} "
            f"--textgame_max_steps {steps} --textgame_no_think {q(no_think)} --total_training_steps {args.total_training_steps}"
        )
    if stage in {"round", "all", "consolidate"}:
        commands.append(
            "bash scripts/textgame_consolidate.sh "
            f"--model {q(model)} --exp_name {q(consolidate_exp)} --nnodes {args.nodes} --oel_round {round_id} "
            f"--kl_loss_type {q(args.kl_loss_type)} --kl_topk {args.kl_topk} --actor_lr {q(args.actor_lr)} "
            f"--experience_max_length {exp_len} --textgame_name {q(textgame)} --max_response_length {resp_len} "
            f"--textgame_max_steps {steps} --textgame_no_think {q(no_think)} --deploy_save_dir <DEPLOY_DATA_DIR> "
            f"--exp_path <EXPERIENCE_LIST> --total_training_steps {args.total_training_steps} --save_freq {args.save_freq}"
        )
    if stage in {"round", "all", "eval"}:
        commands.append(
            "bash scripts/textgame_eval_inturn.sh "
            + q(f"{consolidate_exp},<CKPT_START>,<CKPT_END>,<CKPT_STEP>,{model},false,{resp_len},{textgame},{steps},{no_think}")
        )

    return Plan(
        title="OEL staged round plan",
        summary="Plan extraction, experience-list construction, deploy trajectory collection, consolidation, and evaluation for OEL text games.",
        prerequisites=common_prereqs(args),
        validations=[
            "Validate the generated experience list with scripts/check_experience_inputs.py before consolidation.",
            "Confirm deploy data belongs to the same round, environment, no-think flag, and model family as the experience list.",
        ],
        commands=commands,
        warnings=[
            "These commands are skeletons. Do not execute them from this planner.",
            "OEL requires GPU/Ray/vLLM infrastructure and W&B/HF readiness for real runs.",
        ],
    )


def plan_opcd(args: argparse.Namespace) -> Plan:
    track = args.track or "math"
    stage = args.stage or "on-policy"
    model = placeholder(args.model, "MODEL_OR_ID")
    ref_model = placeholder(args.ref_model, "REF_MODEL_OPTIONAL")
    exp = placeholder(args.exp_name, "EXP_NAME")
    exp_path = placeholder(args.experience_path, "BEST_EXP_OR_PROMPT_PATH")
    commands: List[str] = []
    validations = ["Validate data root or prompt/experience inputs with scripts/check_experience_inputs.py before execution."]

    if track == "math":
        if stage in {"extract", "all"}:
            commands.append("bash scripts/math_extract_inturn.sh")
        if stage in {"on-policy", "consolidate", "all"}:
            commands.append(
                "bash scripts/math_consolidate.sh "
                f"--model {q(model)} --ref_model_path {q(ref_model)} --exp_name {q(exp)} --exp_path {q(exp_path)} "
                f"--nnodes {args.nodes} --rollout_n {args.rollout_n} --kl_loss_type {q(args.kl_loss_type)} "
                f"--kl_topk {args.kl_topk} --actor_lr {q(args.actor_lr)} --max_response_length {args.max_response_length}"
            )
        if stage in {"off-policy", "all"}:
            commands.append(
                "bash scripts/math_generate_offp.sh "
                f"--model {q(model)} --exp_name {q(exp + '-offp-data')} --exp_path {q(exp_path)} --nnodes {args.nodes} "
                f"--rollout_n {args.rollout_n} --kl_loss_type {q(args.kl_loss_type)} --kl_topk {args.kl_topk} "
                f"--actor_lr {q(args.actor_lr)} --max_response_length {args.max_response_length}"
            )
            commands.append(
                "bash scripts/math_train_offp.sh "
                f"--model {q(model)} --ref_model_path {q(ref_model)} --exp_name {q(exp + '-offp-train')} --exp_path {q(exp_path)} "
                f"--nnodes {args.nodes} --rollout_n {args.rollout_n} --kl_loss_type {q(args.kl_loss_type)} --kl_topk {args.kl_topk} "
                f"--actor_lr {q(args.actor_lr)} --off_policy_save_dir <OFF_POLICY_DATA_DIR> --max_response_length {args.max_response_length}"
            )
        if stage in {"eval", "all"}:
            commands.append("bash scripts/math_eval_inturn.sh")
        validations.append("For math, stage dapo_train.parquet, dapo_validation.parquet, and dapo_test.parquet in the target data root.")
    elif track == "textgame":
        textgame = args.textgame_name or "Sokoban-v0"
        no_think = str(args.textgame_no_think).lower()
        base = (
            f"--model {q(model)} --exp_name {q(exp)} --exp_path {q(exp_path)} --nnodes {args.nodes} "
            f"--kl_loss_type {q(args.kl_loss_type)} --kl_topk {args.kl_topk} --actor_lr {q(args.actor_lr)} "
            f"--max_response_length {args.max_response_length} --experience_max_length {args.experience_max_length} "
            f"--textgame_name {q(textgame)} --textgame_max_steps {args.textgame_max_steps} --textgame_no_think {q(no_think)}"
        )
        if stage in {"extract", "all"}:
            commands.append("bash scripts/textgame_extract_inturn.sh")
        if stage in {"on-policy", "consolidate", "all"}:
            commands.append("bash scripts/textgame_consolidate.sh " + base)
        if stage in {"off-policy", "all"}:
            commands.append("bash scripts/textgame_generate_offp.sh " + base.replace(q(exp), q(exp + "-offp-data"), 1))
            commands.append("bash scripts/textgame_train_offp.sh " + base.replace(q(exp), q(exp + "-offp-train"), 1) + " --off_policy_save_dir <OFF_POLICY_DATA_DIR>")
        if stage in {"eval", "all"}:
            commands.append("bash scripts/textgame_eval_inturn.sh")
        validations.append("Keep text-game environment, max steps, no-think flag, and experience path matched across stages.")
    elif track == "system-prompt":
        prompt_type = args.prompt_type or "safety"
        base = (
            f"--model {q(model)} --ref_model_path {q(ref_model)} --exp_name {q(exp)} --exp_path {q(exp_path)} "
            f"--experience_max_length {args.experience_max_length} --nnodes {args.nodes} --rollout_n {args.rollout_n} "
            f"--kl_loss_type {q(args.kl_loss_type)} --kl_topk {args.kl_topk} --actor_lr {q(args.actor_lr)} "
            f"--max_response_length {args.max_response_length} --system_prompt_type {q(prompt_type)}"
        )
        if stage in {"on-policy", "consolidate", "all"}:
            commands.append("bash scripts/sys_consolidate.sh " + base + f" --total_training_steps {args.total_training_steps} --save_freq {args.save_freq}")
        if stage in {"off-policy", "all"}:
            commands.append("bash scripts/sys_generate_offp.sh " + base.replace(q(exp), q(exp + "-offp-data"), 1))
            commands.append("bash scripts/sys_train_offp.sh " + base.replace(q(exp), q(exp + "-offp-train"), 1) + f" --off_policy_save_dir <OFF_POLICY_DATA_DIR> --total_training_steps {args.total_training_steps} --save_freq {args.save_freq}")
        if stage in {"eval", "all"}:
            commands.append("bash scripts/sys_eval_inturn.sh")
        validations.append(f"Validate the {prompt_type} prompt with scripts/check_experience_inputs.py --system-prompt-file <PROMPT_FILE> --prompt-type {prompt_type}.")
    else:
        raise SystemExit(f"Unsupported OPCD track: {track}")

    return Plan(
        title=f"OPCD {track} {stage} plan",
        summary="Plan OPCD context-distillation stages without executing VeRL or data preparation.",
        prerequisites=common_prereqs(args),
        validations=validations,
        commands=commands,
        warnings=["OPCD training/evaluation requires the prepared target environment; this planner does not run it."],
    )


def plan_coach(args: argparse.Namespace) -> Plan:
    stage = args.stage or "train"
    alias = args.alias or "qwen-el-self"
    meta = COACH_ALIASES.get(alias)
    long_name = args.exp_name or (meta["long"] if meta else "<LONG_EXPERIMENT_NAME>")
    commands: List[str] = []
    validations = [
        "Validate EL_DATA_ROOT with scripts/check_experience_inputs.py --profile coach before train/eval.",
        "Use the short alias for usage dispatcher concepts and the long experiment name for scoring/result checks.",
    ]
    warnings = ["Coach training/eval/scoring requires target-host execution; this planner only prints skeletons."]
    if meta is None:
        warnings.append(f"Unknown alias {alias!r}; use --list-coach-aliases to view known aliases.")

    if stage == "list":
        commands.extend([f"# {a}: {m['long']} ({m['mode']}, {m['feedback']})" for a, m in sorted(COACH_ALIASES.items())])
    elif stage == "train":
        commands.append(f"bash usage_example.sh train {q(alias)}")
    elif stage == "eval":
        commands.append(f"bash usage_example.sh eval {q(alias)} {q(placeholder(args.checkpoint, 'CKPT_STEP'))}")
    elif stage in {"eval_fuzzy", "eval-fuzzy"}:
        commands.append(f"bash usage_example.sh eval_fuzzy {q(alias)} {q(placeholder(args.checkpoint, 'CKPT_STEP'))}")
    elif stage in {"eval_endtask", "eval-ifeval"}:
        commands.append(f"bash usage_example.sh eval_endtask {q(alias)} {q(placeholder(args.checkpoint, 'CKPT_STEP'))}")
        warnings.append("IF-Eval uses an unsafe-code-evaluation allowance; require explicit sandbox approval before real execution.")
    elif stage == "score":
        ckpt = placeholder(args.checkpoint, "CKPT_STEP")
        commands.append(
            f"python scripts/eval/eval_gpt4o.py --exp_name {q(long_name)} --start_ckpt {q(ckpt)} --end_ckpt {q(ckpt)}"
        )
        commands.append(
            "python scripts/eval/eval_gpt4o_fuzzy.py --benchmark alpacaeval2,wildbench,arena_hard_v2,creativewritingv3 "
            f"--exp_name {q(long_name)} --start_ckpt {q(ckpt)} --end_ckpt {q(ckpt)}"
        )
        validations.append("Confirm response files exist under EL_RESULT_ROOT before scoring.")
        warnings.append("OpenAI-compatible credentials are required for GPT-4o scoring.")
    else:
        raise SystemExit(f"Unsupported Coach stage: {stage}")

    return Plan(
        title=f"LLM-as-a-Coach {stage} plan",
        summary=f"Plan Coach alias {alias} with long experiment name {long_name}.",
        prerequisites=common_prereqs(args) + [
            "EL_DATA_ROOT, EL_CHECKPOINT_ROOT, and EL_RESULT_ROOT selected for the target host.",
        ],
        validations=validations,
        commands=commands,
        warnings=warnings,
    )


def plan_gad(args: argparse.Namespace) -> Plan:
    stage = args.stage or "warmup"
    model = placeholder(args.model, "STUDENT_MODEL")
    reward_model = placeholder(args.reward_model, "REWARD_MODEL")
    exp = placeholder(args.exp_name, "GAD_EXP")
    commands: List[str] = []
    validations = ["Validate teacher-response parquet files with scripts/check_experience_inputs.py --profile gad."]
    warnings = ["GAD requires branch switching in the VeRL implementation checkout; this planner does not run git commands."]

    if stage == "data-prep":
        commands.append("python tools/export_lmsys_parquet.py  # user-approved dataset export only")
    elif stage == "seqkd":
        commands.extend([
            "cd <GAD_VERL_IMPL> && git checkout seqkd",
            f"cd <GAD_WORKFLOW_DIR> && bash scripts/train/gpt5-chat-filtered-7b-seqkd-lr5e-6.sh --model {q(model)} --exp_name {q(exp)} --nnodes {args.nodes}",
        ])
    elif stage == "warmup":
        commands.extend([
            "cd <GAD_VERL_IMPL> && git checkout warmup",
            f"cd <GAD_WORKFLOW_DIR> && bash scripts/train/gpt5-chat-filtered-7b-warmup-lr1e-6.sh --model {q(model)} --reward_model {q(reward_model)} --exp_name {q(exp)} --nnodes {args.nodes}",
        ])
    elif stage == "adversarial":
        step = placeholder(args.resume_checkpoint or args.checkpoint, "WARMUP_STEP")
        commands.extend([
            "cd <GAD_VERL_IMPL> && git checkout gad",
            "# Stage warmup actor and critic checkpoints into the adversarial experiment namespace before launch.",
            f"cd <GAD_WORKFLOW_DIR> && bash scripts/train/gpt5-chat-filtered-7b-adversarial-lr1e-6.sh --exp_name {q(exp)} --resume_step {q(step)} --nnodes {args.nodes}",
        ])
        validations.append("Confirm actor and critic checkpoint shards exist for the resume step before launch.")
    elif stage in {"generation", "eval"}:
        start = placeholder(args.checkpoint_start, "CKPT_START")
        end = placeholder(args.checkpoint_end, "CKPT_END")
        step = placeholder(args.checkpoint_step, "CKPT_STEP")
        val_data = args.val_data or "lmsys"
        commands.extend([
            "cd <GAD_VERL_IMPL> && git checkout eval",
            f"cd <GAD_WORKFLOW_DIR> && bash scripts/generate/generate.sh --model {q(model)} --exp_name {q(exp)} --val_data {q(val_data)} --ckpt_start {q(start)} --ckpt_end {q(end)} --ckpt_step {q(step)} --nnodes {args.nodes} --ngpus {args.gpus_per_node} --override false",
        ])
    else:
        raise SystemExit(f"Unsupported GAD stage: {stage}")

    return Plan(
        title=f"GAD {stage} plan",
        summary="Plan GAD branch-specific training or generation without executing branch changes or jobs.",
        prerequisites=common_prereqs(args),
        validations=validations,
        commands=commands,
        warnings=warnings,
        notes=["ROUGE-L is a training diagnostic, not a final quality metric."],
    )


def plan_opo(args: argparse.Namespace) -> Plan:
    batch = placeholder(args.batch_size, "GLOBAL_BATCH_SIZE")
    model = placeholder(args.model, "MODEL_OR_ID")
    exp = placeholder(args.exp_name, "OPO_EXP")
    commands = [
        "python -m verl.trainer.main_ppo "
        "algorithm.adv_estimator=grpo "
        f"data.train_batch_size={batch} "
        f"actor_rollout_ref.actor.ppo_mini_batch_size={batch} "
        "actor_rollout_ref.actor.use_kl_loss=False "
        "actor_rollout_ref.actor.kl_loss_coef=0.0 "
        "actor_rollout_ref.actor.entropy_coeff=0.0 "
        "algorithm.kl_ctrl.kl_coef=0.0 "
        f"actor_rollout_ref.model.path={q(model)} "
        f"trainer.experiment_name={q(exp)} "
        "<OTHER_USER_APPROVED_KEYS>",
    ]
    return Plan(
        title="OPO exact on-policy configuration plan",
        summary="Plan exact on-policy hyperparameter changes and optimal reward baseline checks.",
        prerequisites=common_prereqs(args),
        validations=[
            "Confirm train batch size equals PPO mini-batch size.",
            "Confirm actor KL loss is disabled and KL/entropy coefficients are zero.",
            "Confirm the target OPO-modified VeRL checkout includes the optimal reward baseline in the PPO core algorithms module.",
            "Confirm the selected estimator, such as GRPO or Reinforce++, uses the optimal baseline path.",
        ],
        commands=commands,
        warnings=["OPO is a configuration/algorithm recipe; this planner does not inspect or execute VeRL."],
    )


def render_text(plan: Plan) -> str:
    lines: List[str] = []
    lines.append(f"# {plan.title}")
    lines.append("")
    lines.append("SAFE PLAN ONLY: no commands were executed by this script.")
    lines.append("")
    lines.append(plan.summary)
    for label, values in [
        ("Prerequisites", plan.prerequisites),
        ("Validations", plan.validations),
        ("Command skeletons", plan.commands),
        ("Warnings", plan.warnings),
        ("Notes", plan.notes),
    ]:
        if not values:
            continue
        lines.append("")
        lines.append(f"## {label}")
        for item in values:
            if label == "Command skeletons" and not item.startswith("#"):
                lines.append(f"- `{item}`")
            else:
                lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print safe LMOps experiential-learning command plans without executing them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--family", choices=["oel", "opcd", "coach", "gad", "opo"], required=False, help="Workflow family to plan.")
    parser.add_argument("--stage", help="Stage to plan, e.g. round, on-policy, off-policy, train, score, warmup, config.")
    parser.add_argument("--track", choices=["math", "textgame", "system-prompt"], help="OPCD/OEL task track where applicable.")
    parser.add_argument("--model", help="Policy/student/base model identifier or target-host path placeholder.")
    parser.add_argument("--ref-model", help="Reference/teacher model identifier for OPCD or OPO ports.")
    parser.add_argument("--reward-model", help="Reward/discriminator model identifier for GAD warmup.")
    parser.add_argument("--exp-model", help="Experiential/coach model identifier where supported.")
    parser.add_argument("--exp-name", help="Experiment name or long Coach experiment name.")
    parser.add_argument("--alias", help="LLM-as-a-Coach short alias.")
    parser.add_argument("--checkpoint", help="Single checkpoint step.")
    parser.add_argument("--checkpoint-start", help="Checkpoint range start.")
    parser.add_argument("--checkpoint-end", help="Checkpoint range end.")
    parser.add_argument("--checkpoint-step", help="Checkpoint range step.")
    parser.add_argument("--resume-checkpoint", help="Resume checkpoint step for OEL/GAD.")
    parser.add_argument("--experience-path", help="Experience list, best experience path, or system prompt file placeholder.")
    parser.add_argument("--prompt-type", choices=["medmcqa", "safety", "custom"], help="OPCD system prompt type.")
    parser.add_argument("--round", type=int, default=1, help="OEL round number.")
    parser.add_argument("--prompt-version", default="v4", help="OEL/OPCD extraction prompt version.")
    parser.add_argument("--val-samples-limit", type=int, default=100, help="Extraction validation sample limit.")
    parser.add_argument("--val-samples-use", type=int, default=50, help="Selected validation sample count for make_exp_list.")
    parser.add_argument("--exp-sel-with-prev", default="true", help="Whether extraction includes previous experience in context.")
    parser.add_argument("--textgame-name", help="Text-game environment name.")
    parser.add_argument("--textgame-max-steps", type=int, default=5, help="Maximum text-game steps.")
    parser.add_argument("--textgame-no-think", default="true", help="Whether to use no-think text-game prompting.")
    parser.add_argument("--textgame-response-length", type=int, default=1024, help="Text-game response length during extraction.")
    parser.add_argument("--experience-max-length", type=int, default=8192, help="Experience/system-prompt max length.")
    parser.add_argument("--max-response-length", type=int, default=1024, help="Model response length.")
    parser.add_argument("--nodes", type=int, default=1, help="Node count.")
    parser.add_argument("--gpus-per-node", type=int, default=8, help="GPUs per node.")
    parser.add_argument("--gpu-class", choices=["a100", "h100", "h200", "b200", "other", "unknown"], default="unknown", help="GPU class for setup caveats.")
    parser.add_argument("--rollout-n", type=int, default=1, help="Rollout count where applicable.")
    parser.add_argument("--actor-lr", default="5e-6", help="Actor learning rate.")
    parser.add_argument("--kl-loss-type", default="full", help="KL loss type for OPCD/OEL-style consolidation.")
    parser.add_argument("--kl-topk", type=int, default=256, help="KL top-k value.")
    parser.add_argument("--total-training-steps", type=int, default=100, help="Total training steps for staged examples.")
    parser.add_argument("--save-freq", type=int, default=2, help="Checkpoint save frequency.")
    parser.add_argument("--batch-size", help="Global batch size for OPO exact on-policy config.")
    parser.add_argument("--val-data", help="GAD validation data name for generation.")
    parser.add_argument("--credentials", help="Comma-separated credential surfaces to check: wandb,hf,openai.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown text.")
    parser.add_argument("--list-coach-aliases", action="store_true", help="List Coach aliases and exit.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_coach_aliases:
        for alias, meta in sorted(COACH_ALIASES.items()):
            print(f"{alias}\t{meta['long']}\t{meta['mode']}\t{meta['feedback']}")
        return 0

    if not args.family:
        parser.error("--family is required unless --list-coach-aliases is used")

    if args.family == "oel":
        plan = plan_oel(args)
    elif args.family == "opcd":
        plan = plan_opcd(args)
    elif args.family == "coach":
        plan = plan_coach(args)
    elif args.family == "gad":
        plan = plan_gad(args)
    elif args.family == "opo":
        plan = plan_opo(args)
    else:  # pragma: no cover: argparse prevents this
        raise SystemExit(f"Unsupported family: {args.family}")

    if args.json:
        print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
    else:
        sys.stdout.write(render_text(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
