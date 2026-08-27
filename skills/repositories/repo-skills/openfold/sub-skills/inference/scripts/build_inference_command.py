#!/usr/bin/env python3
"""Build dry-run OpenFold inference commands without importing OpenFold."""

from __future__ import print_function

import argparse
import shlex
import sys
from pathlib import Path


RUN_DATABASE_FLAGS = (
    ("uniref90_database_path", "--uniref90_database_path"),
    ("mgnify_database_path", "--mgnify_database_path"),
    ("pdb70_database_path", "--pdb70_database_path"),
    ("pdb_seqres_database_path", "--pdb_seqres_database_path"),
    ("uniref30_database_path", "--uniref30_database_path"),
    ("uniclust30_database_path", "--uniclust30_database_path"),
    ("uniprot_database_path", "--uniprot_database_path"),
    ("bfd_database_path", "--bfd_database_path"),
)

BINARY_FLAGS = (
    ("jackhmmer_binary_path", "--jackhmmer_binary_path"),
    ("hhblits_binary_path", "--hhblits_binary_path"),
    ("hhsearch_binary_path", "--hhsearch_binary_path"),
    ("hmmsearch_binary_path", "--hmmsearch_binary_path"),
    ("hmmbuild_binary_path", "--hmmbuild_binary_path"),
    ("kalign_binary_path", "--kalign_binary_path"),
)

TEMPLATE_METADATA_FLAGS = (
    ("max_template_date", "--max_template_date"),
    ("obsolete_pdbs_path", "--obsolete_pdbs_path"),
    ("release_dates_path", "--release_dates_path"),
)


def add_option(command, flag, value):
    if value not in (None, ""):
        command.extend([flag, str(value)])


def add_bool(command, flag, enabled):
    if enabled:
        command.append(flag)


def check_path(value, label, require_existing_paths, errors, expect_dir=None):
    if not value or not require_existing_paths:
        return
    path = Path(value)
    if not path.exists():
        errors.append("{} does not exist: {}".format(label, value))
        return
    if expect_dir is True and not path.is_dir():
        errors.append("{} is not a directory: {}".format(label, value))
    if expect_dir is False and not path.is_file():
        errors.append("{} is not a file: {}".format(label, value))


def default_config_for_mode(mode, explicit):
    if explicit:
        return explicit
    if mode == "multimer":
        return "model_1_multimer_v3"
    if mode == "soloseq":
        return "seq_model_esm1b_ptm"
    return "model_1_ptm"


def validate_run_args(args):
    errors = []
    check_path(args.fasta_dir, "FASTA directory", args.require_existing_paths, errors, expect_dir=True)
    check_path(args.template_mmcif_dir, "template mmCIF directory", args.require_existing_paths, errors, expect_dir=True)
    check_path(args.use_precomputed_alignments, "precomputed alignment directory", args.require_existing_paths, errors, expect_dir=True)
    check_path(args.openfold_checkpoint_path, "OpenFold checkpoint path", args.require_existing_paths, errors)
    check_path(args.jax_param_path, "JAX parameter path", args.require_existing_paths, errors, expect_dir=False)
    check_path(args.experiment_config_json, "experiment config JSON", args.require_existing_paths, errors, expect_dir=False)

    config_preset = default_config_for_mode(args.mode, args.config_preset)

    if args.mode == "multimer":
        if "multimer" not in config_preset:
            errors.append("multimer mode should use a multimer preset such as model_1_multimer_v3")
        if args.openfold_checkpoint_path:
            errors.append("documented multimer mode uses AlphaFold multimer parameters; omit --openfold-checkpoint-path unless model-api guidance says it is compatible")
        if not args.use_precomputed_alignments:
            required = (
                "uniref90_database_path",
                "mgnify_database_path",
                "pdb_seqres_database_path",
                "uniref30_database_path",
                "uniprot_database_path",
                "bfd_database_path",
                "hmmsearch_binary_path",
                "hmmbuild_binary_path",
            )
            missing = [name for name in required if not getattr(args, name)]
            if missing:
                errors.append("multimer without precomputed alignments is missing: " + ", ".join(missing))
            if args.pdb70_database_path and not args.pdb_seqres_database_path:
                errors.append("multimer template search should use PDB SeqRes/HMMSearch, not only PDB70/HHSearch")
    elif args.mode == "soloseq":
        if not config_preset.startswith("seq"):
            errors.append("SoloSeq mode should use a seq preset such as seq_model_esm1b_ptm")
        if not args.openfold_checkpoint_path:
            errors.append("SoloSeq planning should include --openfold-checkpoint-path for the SoloSeq checkpoint")
        if not args.use_precomputed_alignments and not args.skip_templates:
            required = (
                "uniref90_database_path",
                "pdb70_database_path",
                "jackhmmer_binary_path",
                "hhsearch_binary_path",
                "kalign_binary_path",
            )
            missing = [name for name in required if not getattr(args, name)]
            if missing:
                errors.append(
                    "SoloSeq on-the-fly template generation is missing: "
                    + ", ".join(missing)
                    + "; pass --skip-templates if template-free SoloSeq is intentional"
                )
    else:
        if "multimer" in config_preset:
            errors.append("monomer mode should not use a multimer config preset")
        if config_preset.startswith("seq"):
            errors.append("monomer mode should not use a SoloSeq config preset")
        if not args.use_precomputed_alignments:
            required = ("uniref90_database_path", "mgnify_database_path")
            missing = [name for name in required if not getattr(args, name)]
            if missing:
                errors.append("monomer without precomputed alignments is missing: " + ", ".join(missing))
            if not args.pdb70_database_path and not args.use_custom_template and not args.skip_templates:
                errors.append("monomer template search usually needs --pdb70-database-path unless custom/template-free planning is intentional")
            if not args.bfd_database_path and not (args.uniclust30_database_path or args.uniref30_database_path):
                errors.append("monomer MSA planning usually needs --bfd-database-path and either --uniclust30-database-path or --uniref30-database-path")

    if args.use_custom_template and args.mode == "multimer":
        errors.append("custom template mode is documented for monomer-style template featurization; do not combine it with multimer planning without model-api review")
    if args.trt_mode and not args.trt_engine_dir:
        errors.append("--trt-mode requires --trt-engine-dir")
    if args.trt_optimization_level is not None and not 0 <= args.trt_optimization_level <= 5:
        errors.append("--trt-optimization-level must be between 0 and 5")
    if args.trt_max_sequence_len is not None and args.trt_max_sequence_len <= 0:
        errors.append("--trt-max-sequence-len must be positive")
    if args.cpus is not None and args.cpus <= 0:
        errors.append("--cpus must be positive")
    return errors


def build_run_command(args):
    command = [args.python, args.run_script, args.fasta_dir, args.template_mmcif_dir]
    add_option(command, "--output_dir", args.output_dir)
    add_option(command, "--config_preset", default_config_for_mode(args.mode, args.config_preset))
    add_option(command, "--model_device", args.model_device)
    add_option(command, "--jax_param_path", args.jax_param_path)
    add_option(command, "--openfold_checkpoint_path", args.openfold_checkpoint_path)
    add_option(command, "--use_precomputed_alignments", args.use_precomputed_alignments)
    add_bool(command, "--use_custom_template", args.use_custom_template)
    add_bool(command, "--use_single_seq_mode", args.mode == "soloseq" or args.use_single_seq_mode)

    for attr, flag in RUN_DATABASE_FLAGS:
        add_option(command, flag, getattr(args, attr))
    for attr, flag in BINARY_FLAGS:
        add_option(command, flag, getattr(args, attr))
    for attr, flag in TEMPLATE_METADATA_FLAGS:
        add_option(command, flag, getattr(args, attr))

    add_option(command, "--cpus", args.cpus)
    add_option(command, "--preset", args.database_preset)
    add_option(command, "--output_postfix", args.output_postfix)
    add_option(command, "--data_random_seed", args.data_random_seed)
    add_option(command, "--multimer_ri_gap", args.multimer_ri_gap)
    add_option(command, "--experiment_config_json", args.experiment_config_json)
    add_option(command, "--precision", args.precision)
    add_option(command, "--trt_mode", args.trt_mode)
    add_option(command, "--trt_engine_dir", args.trt_engine_dir)
    add_option(command, "--trt_max_sequence_len", args.trt_max_sequence_len)
    add_option(command, "--trt_num_profiles", args.trt_num_profiles)
    add_option(command, "--trt_optimization_level", args.trt_optimization_level)

    add_bool(command, "--save_outputs", args.save_outputs)
    add_bool(command, "--skip_relaxation", args.skip_relaxation)
    add_bool(command, "--trace_model", args.trace_model)
    add_bool(command, "--subtract_plddt", args.subtract_plddt)
    add_bool(command, "--long_sequence_inference", args.long_sequence_inference)
    add_bool(command, "--cif_output", args.cif_output)
    add_bool(command, "--use_deepspeed_evoformer_attention", args.use_deepspeed_evoformer_attention)
    add_bool(command, "--use_cuequivariance_attention", args.use_cuequivariance_attention)
    add_bool(command, "--use_cuequivariance_multiplicative_update", args.use_cuequivariance_multiplicative_update)
    return command


def validate_thread_args(args):
    errors = []
    check_path(args.input_fasta, "input FASTA", args.require_existing_paths, errors, expect_dir=False)
    check_path(args.input_mmcif, "input mmCIF", args.require_existing_paths, errors, expect_dir=False)
    check_path(args.openfold_checkpoint_path, "OpenFold checkpoint path", args.require_existing_paths, errors)
    check_path(args.jax_param_path, "JAX parameter path", args.require_existing_paths, errors, expect_dir=False)
    if not args.template_id:
        errors.append("threading should include --template-id for traceable output metadata")
    if not args.chain_id:
        errors.append("threading should include --chain-id for template chain selection")
    if args.config_preset and "multimer" in args.config_preset:
        errors.append("thread_sequence.py is a single-sequence workflow; do not use a multimer preset")
    return errors


def build_thread_command(args):
    command = [args.python, args.thread_script, args.input_fasta, args.input_mmcif]
    add_option(command, "--template_id", args.template_id)
    add_option(command, "--chain_id", args.chain_id)
    add_option(command, "--model_device", args.model_device)
    add_option(command, "--config_preset", args.config_preset or "model_1")
    add_option(command, "--jax_param_path", args.jax_param_path)
    add_option(command, "--openfold_checkpoint_path", args.openfold_checkpoint_path)
    add_option(command, "--output_dir", args.output_dir)
    add_option(command, "--data_random_seed", args.data_random_seed)
    add_option(command, "--kalign_binary_path", args.kalign_binary_path)
    for attr, flag in TEMPLATE_METADATA_FLAGS:
        add_option(command, flag, getattr(args, attr))
    add_bool(command, "--subtract_plddt", args.subtract_plddt)
    return command


def add_database_and_binary_flags(parser):
    for attr, _flag in RUN_DATABASE_FLAGS:
        parser.add_argument("--" + attr.replace("_", "-"), dest=attr)
    for attr, _flag in BINARY_FLAGS:
        parser.add_argument("--" + attr.replace("_", "-"), dest=attr)
    for attr, _flag in TEMPLATE_METADATA_FLAGS:
        parser.add_argument("--" + attr.replace("_", "-"), dest=attr)


def add_run_flags(parser):
    parser.add_argument("--python", default="python", help="Python executable token to print in the command")
    parser.add_argument("--run-script", default="run_pretrained_openfold.py", help="Path or token for the OpenFold inference script")
    parser.add_argument("--mode", choices=("monomer", "multimer", "soloseq"), default="monomer")
    parser.add_argument("--fasta-dir", required=True, dest="fasta_dir")
    parser.add_argument("--template-mmcif-dir", required=True, dest="template_mmcif_dir")
    parser.add_argument("--output-dir", required=True, dest="output_dir")
    parser.add_argument("--config-preset", dest="config_preset")
    parser.add_argument("--model-device", default="cpu", dest="model_device")
    parser.add_argument("--jax-param-path", dest="jax_param_path")
    parser.add_argument("--openfold-checkpoint-path", dest="openfold_checkpoint_path")
    parser.add_argument("--use-precomputed-alignments", dest="use_precomputed_alignments")
    parser.add_argument("--use-custom-template", action="store_true", dest="use_custom_template")
    parser.add_argument("--use-single-seq-mode", action="store_true", dest="use_single_seq_mode")
    parser.add_argument("--skip-templates", action="store_true", help="Declare template-free planning intentional")
    add_database_and_binary_flags(parser)
    parser.add_argument("--cpus", type=int)
    parser.add_argument("--database-preset", choices=("full_dbs", "reduced_dbs"), dest="database_preset")
    parser.add_argument("--output-postfix", dest="output_postfix")
    parser.add_argument("--data-random-seed", type=int, dest="data_random_seed")
    parser.add_argument("--skip-relaxation", action="store_true", dest="skip_relaxation")
    parser.add_argument("--multimer-ri-gap", type=int, dest="multimer_ri_gap")
    parser.add_argument("--trace-model", action="store_true", dest="trace_model")
    parser.add_argument("--subtract-plddt", action="store_true", dest="subtract_plddt")
    parser.add_argument("--long-sequence-inference", action="store_true", dest="long_sequence_inference")
    parser.add_argument("--cif-output", action="store_true", dest="cif_output")
    parser.add_argument("--experiment-config-json", dest="experiment_config_json")
    parser.add_argument("--use-deepspeed-evoformer-attention", action="store_true", dest="use_deepspeed_evoformer_attention")
    parser.add_argument("--use-cuequivariance-attention", action="store_true", dest="use_cuequivariance_attention")
    parser.add_argument("--use-cuequivariance-multiplicative-update", action="store_true", dest="use_cuequivariance_multiplicative_update")
    parser.add_argument("--trt-mode", choices=("build", "run"), dest="trt_mode")
    parser.add_argument("--trt-engine-dir", dest="trt_engine_dir")
    parser.add_argument("--precision", choices=("tf32", "fp32", "fp16", "bf16"), default="tf32")
    parser.add_argument("--trt-max-sequence-len", type=int, dest="trt_max_sequence_len")
    parser.add_argument("--trt-num-profiles", type=int, dest="trt_num_profiles")
    parser.add_argument("--trt-optimization-level", type=int, dest="trt_optimization_level")
    parser.add_argument("--save-outputs", action="store_true", dest="save_outputs")
    parser.add_argument("--require-existing-paths", action="store_true", help="Fail if provided input/checkpoint/config paths do not exist")


def add_thread_flags(parser):
    parser.add_argument("--python", default="python", help="Python executable token to print in the command")
    parser.add_argument("--thread-script", default="thread_sequence.py", help="Path or token for the OpenFold threading script")
    parser.add_argument("--input-fasta", required=True, dest="input_fasta")
    parser.add_argument("--input-mmcif", required=True, dest="input_mmcif")
    parser.add_argument("--template-id", dest="template_id")
    parser.add_argument("--chain-id", dest="chain_id")
    parser.add_argument("--model-device", default="cpu", dest="model_device")
    parser.add_argument("--config-preset", default="model_1", dest="config_preset")
    parser.add_argument("--jax-param-path", dest="jax_param_path")
    parser.add_argument("--openfold-checkpoint-path", dest="openfold_checkpoint_path")
    parser.add_argument("--output-dir", required=True, dest="output_dir")
    parser.add_argument("--subtract-plddt", action="store_true", dest="subtract_plddt")
    parser.add_argument("--data-random-seed", dest="data_random_seed")
    parser.add_argument("--kalign-binary-path", dest="kalign_binary_path")
    for attr, _flag in TEMPLATE_METADATA_FLAGS:
        parser.add_argument("--" + attr.replace("_", "-"), dest=attr)
    parser.add_argument("--require-existing-paths", action="store_true", help="Fail if provided input/checkpoint paths do not exist")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    try:
        subparsers.required = True
    except AttributeError:
        pass

    run_parser = subparsers.add_parser("run", help="Build a run_pretrained_openfold.py command")
    add_run_flags(run_parser)

    thread_parser = subparsers.add_parser("thread", help="Build a thread_sequence.py command")
    add_thread_flags(thread_parser)

    args = parser.parse_args(argv)
    if args.command == "run":
        errors = validate_run_args(args)
        command = build_run_command(args)
    elif args.command == "thread":
        errors = validate_thread_args(args)
        command = build_thread_command(args)
    else:
        parser.error("choose a subcommand")

    if errors:
        for error in errors:
            print("error: " + error, file=sys.stderr)
        return 2

    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
