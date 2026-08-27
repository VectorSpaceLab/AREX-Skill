#!/usr/bin/env python3
"""Dry-run OpenFold parameter and database asset planner.

This script prints workflow-specific prerequisites, expected asset paths, and
retrieval notes. It never downloads, executes shell commands, invokes network
clients, or creates files.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Asset:
    name: str
    required_for: str
    destination: str
    expected_paths: list[str]
    retrieval_notes: list[str]
    prerequisites: list[str]
    notes: list[str]


PARAMETER_SOURCES = {
    "alphafold": "Equivalent source workflow: AlphaFold parameter archive. Place params_model_*.npz under {params_dir} or pass --jax_param_path.",
    "openfold": "Equivalent source workflow: OpenFold checkpoint release. Place .pt checkpoints under {params_dir} or pass --openfold_checkpoint_path.",
    "openfold-gdrive": "Alternate source: OpenFold Google Drive checkpoint archive when default object storage is unavailable.",
    "openfold-huggingface": "Alternate source: OpenFold Hugging Face checkpoint repository when Git LFS access is available.",
    "soloseq": "Equivalent source workflow: OpenFold SoloSeq parameter release. Use seq_model_esm1b_ptm.pt with --openfold_checkpoint_path.",
}

DATABASE_SOURCES = {
    "alphafold_dbs": "Equivalent source workflow: OpenFold-maintained AlphaFold database acquisition for monomer databases under {base_data_dir}.",
    "bfd": "Acquire the full BFD database under {base_data_dir}/bfd before monomer or multimer MSA generation.",
    "small_bfd": "Acquire the reduced Small BFD database under {base_data_dir}/small_bfd when using the reduced database preset.",
    "mgnify": "Acquire MGnify under {base_data_dir}/mgnify.",
    "pdb70": "Acquire PDB70 under {base_data_dir}/pdb70 for monomer HHSearch template search.",
    "pdb_mmcif": "Acquire PDB mmCIF template files under {base_data_dir}/pdb_mmcif/mmcif_files.",
    "pdb_seqres": "Acquire PDB SeqRes under {base_data_dir}/pdb_seqres for multimer HMMSearch template search.",
    "uniclust30": "Acquire UniClust30 under {base_data_dir}/uniclust30 for monomer HHblits workflows.",
    "uniref30": "Acquire UniRef30 under {base_data_dir}/uniref30 for multimer workflows.",
    "uniref90": "Acquire UniRef90 under {base_data_dir}/uniref90 for JackHMMER workflows.",
    "uniprot": "Acquire UniProt under {base_data_dir}/uniprot for multimer workflows.",
    "mmseqs_dbs": "Acquire MMseqs databases under {base_data_dir} only for MMseqs-based alignment workflows.",
    "colabfold_envdb": "Acquire ColabFold environmental databases under {base_data_dir} only for ColabFold/MMseqs workflows.",
    "soloseq_embeddings": "Provide or precompute SoloSeq ESM embeddings in the configured embeddings directory.",
}


def source_note(template: str, params_dir: str, base_data_dir: str) -> str:
    return template.format(params_dir=params_dir, base_data_dir=base_data_dir)


def parameter_assets(workflow: str, parameter_set: str, params_dir: str, base_data_dir: str) -> list[Asset]:
    del base_data_dir
    assets: list[Asset] = []
    include_alphafold = parameter_set in {"alphafold", "both", "auto"}
    include_openfold = parameter_set in {"openfold", "both", "auto"}

    if workflow == "multimer":
        include_alphafold = True
        include_openfold = parameter_set in {"openfold", "both"}

    if workflow == "soloseq":
        return [
            Asset(
                name="OpenFold SoloSeq parameters",
                required_for="SoloSeq single-sequence inference with seq_model_esm1b_ptm",
                destination=params_dir,
                expected_paths=[str(Path(params_dir) / "openfold_soloseq_params" / "seq_model_esm1b_ptm.pt")],
                retrieval_notes=[source_note(PARAMETER_SOURCES["soloseq"], params_dir, "data")],
                prerequisites=["network access", "sufficient storage", "checkpoint/license review"],
                notes=["Use --openfold_checkpoint_path to point at seq_model_esm1b_ptm.pt.", "ESM-1b embeddings limit SoloSeq sequences to 1022 residues."],
            )
        ]

    if include_alphafold:
        label = "AlphaFold-Multimer v2.3 parameters" if workflow == "multimer" else "AlphaFold monomer parameters"
        assets.append(
            Asset(
                name=label,
                required_for="AlphaFold parameter inference presets",
                destination=params_dir,
                expected_paths=[str(Path(params_dir) / "params_model_*.npz"), str(Path(params_dir) / "params" / "params_model_*.npz")],
                retrieval_notes=[source_note(PARAMETER_SOURCES["alphafold"], params_dir, "data")],
                prerequisites=["network access", "sufficient storage", "parameter license review", "aria2c or equivalent downloader"],
                notes=["DeepMind AlphaFold parameters are CC BY 4.0.", "When not using default resource layout, pass --jax_param_path for the selected .npz file."],
            )
        )

    if include_openfold and workflow != "multimer":
        assets.append(
            Asset(
                name="OpenFold monomer parameters",
                required_for="OpenFold checkpoint inference presets",
                destination=params_dir,
                expected_paths=[str(Path(params_dir) / "openfold_params" / "*.pt"), str(Path(params_dir) / "*.pt")],
                retrieval_notes=[
                    source_note(PARAMETER_SOURCES["openfold"], params_dir, "data"),
                    source_note(PARAMETER_SOURCES["openfold-gdrive"], params_dir, "data"),
                    source_note(PARAMETER_SOURCES["openfold-huggingface"], params_dir, "data"),
                ],
                prerequisites=["network access", "sufficient storage", "aws, browser/GDrive, or Git LFS tooling depending on chosen source"],
                notes=["Use --openfold_checkpoint_path for a selected .pt or DeepSpeed checkpoint.", "Choose no-template and pTM checkpoints to match config preset intent."],
            )
        )

    return assets


def monomer_database_assets(base_data_dir: str, small_bfd: bool) -> list[Asset]:
    bfd_key = "small_bfd" if small_bfd else "bfd"
    bfd_name = "Small BFD" if small_bfd else "BFD"
    bfd_expected = "small_bfd/bfd-first_non_consensus_sequences.fasta" if small_bfd else "bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt"
    return [
        Asset(
            name="PDB mmCIF templates",
            required_for="Template featurization and template directory positional argument",
            destination=base_data_dir,
            expected_paths=[str(Path(base_data_dir) / "pdb_mmcif" / "mmcif_files"), str(Path(base_data_dir) / "pdb_mmcif" / "obsolete.dat")],
            retrieval_notes=[source_note(DATABASE_SOURCES["pdb_mmcif"], "openfold/resources", base_data_dir)],
            prerequisites=["network access", "large storage", "template date/version tracking", "aria2c or equivalent downloader"],
            notes=["Keep PDB mmCIF date synchronized with PDB SeqRes if later upgrading to multimer."],
        ),
        Asset(
            name="UniRef90",
            required_for="Monomer MSA generation with JackHMMER",
            destination=base_data_dir,
            expected_paths=[str(Path(base_data_dir) / "uniref90" / "uniref90.fasta")],
            retrieval_notes=[source_note(DATABASE_SOURCES["uniref90"], "openfold/resources", base_data_dir)],
            prerequisites=["network access", "large storage", "jackhmmer"],
            notes=["Can be skipped when every query uses valid precomputed alignments."],
        ),
        Asset(
            name="MGnify",
            required_for="Monomer MSA generation",
            destination=base_data_dir,
            expected_paths=[str(Path(base_data_dir) / "mgnify" / "mgy_clusters_*.fa")],
            retrieval_notes=[source_note(DATABASE_SOURCES["mgnify"], "openfold/resources", base_data_dir)],
            prerequisites=["network access", "large storage", "jackhmmer"],
            notes=["Use the MGnify release expected by the selected OpenFold/AlphaFold database plan."],
        ),
        Asset(
            name=bfd_name,
            required_for="Monomer MSA generation",
            destination=base_data_dir,
            expected_paths=[str(Path(base_data_dir) / bfd_expected)],
            retrieval_notes=[source_note(DATABASE_SOURCES[bfd_key], "openfold/resources", base_data_dir)],
            prerequisites=["network access", "large storage", "hhblits"],
            notes=["Small BFD reduces storage but may change quality trade-offs." if small_bfd else "Full BFD is storage-heavy; confirm disk budget before download."],
        ),
        Asset(
            name="UniClust30",
            required_for="Monomer MSA generation with HHblits",
            destination=base_data_dir,
            expected_paths=[str(Path(base_data_dir) / "uniclust30" / "uniclust30_*" / "uniclust30_*")],
            retrieval_notes=[source_note(DATABASE_SOURCES["uniclust30"], "openfold/resources", base_data_dir)],
            prerequisites=["network access", "large storage", "hhblits"],
            notes=["Some newer multimer workflows use UniRef30 instead."],
        ),
        Asset(
            name="PDB70",
            required_for="Monomer template search with HHSearch",
            destination=base_data_dir,
            expected_paths=[str(Path(base_data_dir) / "pdb70" / "pdb70")],
            retrieval_notes=[source_note(DATABASE_SOURCES["pdb70"], "openfold/resources", base_data_dir)],
            prerequisites=["network access", "large storage", "hhsearch"],
            notes=["Can be skipped when precomputed alignments already include hhsearch_output.hhr."],
        ),
    ]


def multimer_database_assets(base_data_dir: str, small_bfd: bool) -> list[Asset]:
    assets = [asset for asset in monomer_database_assets(base_data_dir, small_bfd) if asset.name not in {"UniClust30", "PDB70"}]
    assets.extend(
        [
            Asset(
                name="PDB SeqRes",
                required_for="Multimer template search with HMMSearch",
                destination=base_data_dir,
                expected_paths=[str(Path(base_data_dir) / "pdb_seqres" / "pdb_seqres.txt")],
                retrieval_notes=[source_note(DATABASE_SOURCES["pdb_seqres"], "openfold/resources", base_data_dir)],
                prerequisites=["network access", "large storage", "hmmsearch", "hmmbuild"],
                notes=["Keep PDB SeqRes and PDB mmCIF from the same date to avoid template search errors."],
            ),
            Asset(
                name="UniRef30",
                required_for="Multimer MSA generation",
                destination=base_data_dir,
                expected_paths=[str(Path(base_data_dir) / "uniref30" / "UniRef30_*")],
                retrieval_notes=[source_note(DATABASE_SOURCES["uniref30"], "openfold/resources", base_data_dir)],
                prerequisites=["network access", "large storage", "hhblits"],
                notes=["Multimer docs use UniRef30 rather than older UniClust30 naming."],
            ),
            Asset(
                name="UniProt",
                required_for="Multimer MSA generation",
                destination=base_data_dir,
                expected_paths=[str(Path(base_data_dir) / "uniprot" / "uniprot.fasta")],
                retrieval_notes=[source_note(DATABASE_SOURCES["uniprot"], "openfold/resources", base_data_dir)],
                prerequisites=["network access", "large storage", "jackhmmer"],
                notes=["Required for AlphaFold-Multimer-style database searches."],
            ),
        ]
    )
    return assets


def soloseq_assets(base_data_dir: str, params_dir: str, include_templates: bool) -> list[Asset]:
    assets = parameter_assets("soloseq", "auto", params_dir, base_data_dir)
    assets.append(
        Asset(
            name="SoloSeq ESM embeddings or generation runtime",
            required_for="Single-sequence inference with seq_model_esm1b_ptm",
            destination=base_data_dir,
            expected_paths=["embedding directory containing one subdirectory per FASTA label"],
            retrieval_notes=[source_note(DATABASE_SOURCES["soloseq_embeddings"], params_dir, base_data_dir)],
            prerequisites=["ESM model/runtime dependencies", "GPU recommended", "network/cache planning if ESM weights are not already available"],
            notes=["The planner does not download ESM weights or run embedding generation.", "Template-free SoloSeq can omit template search databases."],
        )
    )
    if include_templates:
        assets.extend(
            [
                Asset(
                    name="UniRef90 for SoloSeq template-assisted mode",
                    required_for="Optional generated HHSearch template evidence",
                    destination=base_data_dir,
                    expected_paths=[str(Path(base_data_dir) / "uniref90" / "uniref90.fasta")],
                    retrieval_notes=[source_note(DATABASE_SOURCES["uniref90"], params_dir, base_data_dir)],
                    prerequisites=["network access", "jackhmmer"],
                    notes=["Only needed when generating template information instead of using embedding-only inference."],
                ),
                Asset(
                    name="PDB70 and PDB mmCIF for SoloSeq templates",
                    required_for="Optional template search and template featurization",
                    destination=base_data_dir,
                    expected_paths=[str(Path(base_data_dir) / "pdb70" / "pdb70"), str(Path(base_data_dir) / "pdb_mmcif" / "mmcif_files")],
                    retrieval_notes=[source_note(DATABASE_SOURCES["pdb70"], params_dir, base_data_dir), source_note(DATABASE_SOURCES["pdb_mmcif"], params_dir, base_data_dir)],
                    prerequisites=["network access", "hhsearch", "kalign"],
                    notes=["Can be skipped for template-free SoloSeq."],
                ),
            ]
        )
    return assets


def training_assets(base_data_dir: str, params_dir: str, small_bfd: bool) -> list[Asset]:
    assets = parameter_assets("monomer", "openfold", params_dir, base_data_dir)
    assets.append(
        Asset(
            name="OpenProteinSet training data",
            required_for="Training and fine-tuning OpenFold",
            destination=base_data_dir,
            expected_paths=[
                str(Path(base_data_dir) / "alignment_data" / "alignments"),
                str(Path(base_data_dir) / "alignment_data" / "alignment_db"),
                str(Path(base_data_dir) / "pdb_data" / "mmcifs"),
                str(Path(base_data_dir) / "pdb_data" / "data_caches"),
                str(Path(base_data_dir) / "pdb_data" / "obsolete.dat"),
            ],
            retrieval_notes=[
                "Equivalent source workflow: OpenFold public training-data object storage for alignments, mmCIF archives, and data caches.",
                "After retrieval, route alignment DB, duplicate-chain, cluster, mmCIF-cache, and chain-cache layout work to ../data-preparation/.",
            ],
            prerequisites=["awscli or equivalent object-store tooling", "very large storage", "postprocessing via data-preparation workflows"],
            notes=["Route training command construction to ../training/.", "CPU-only training is not supported for practical OpenFold training workflows."],
        )
    )
    assets.extend(monomer_database_assets(base_data_dir, small_bfd))
    return assets


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    workflow = args.workflow
    if workflow == "monomer":
        assets = parameter_assets(workflow, args.parameter_set, args.params_dir, args.base_data_dir)
        if not args.precomputed_alignments:
            assets.extend(monomer_database_assets(args.base_data_dir, args.small_bfd))
    elif workflow == "multimer":
        assets = parameter_assets(workflow, args.parameter_set, args.params_dir, args.base_data_dir)
        if not args.precomputed_alignments:
            assets.extend(multimer_database_assets(args.base_data_dir, args.small_bfd))
    elif workflow == "soloseq":
        assets = soloseq_assets(args.base_data_dir, args.params_dir, args.include_templates)
    elif workflow == "training":
        assets = training_assets(args.base_data_dir, args.params_dir, args.small_bfd)
    else:
        assets = []
        for nested in ["monomer", "multimer", "soloseq", "training"]:
            nested_args = argparse.Namespace(**{**vars(args), "workflow": nested})
            nested_plan = build_plan(nested_args)
            for asset_dict in nested_plan["assets"]:
                asset = Asset(**asset_dict)
                assets.append(
                    Asset(
                        name=f"[{nested}] {asset.name}",
                        required_for=asset.required_for,
                        destination=asset.destination,
                        expected_paths=asset.expected_paths,
                        retrieval_notes=asset.retrieval_notes,
                        prerequisites=asset.prerequisites,
                        notes=asset.notes,
                    )
                )

    warnings: list[str] = []
    if args.precomputed_alignments and workflow in {"monomer", "multimer"}:
        warnings.append("Precomputed alignments selected: sequence databases may be skipped only if every query has a valid alignment/template output layout.")
    if workflow == "multimer":
        warnings.append("Multimer requires AlphaFold-Multimer parameters and PDB SeqRes/PDB mmCIF assets from compatible dates.")
    if workflow == "soloseq":
        warnings.append("SoloSeq ESM-1b embeddings truncate sequences longer than 1022 residues.")
    if workflow == "training":
        warnings.append("Training data acquisition and preprocessing are storage-heavy; route layout work to ../data-preparation/ and execution to ../training/.")

    return {
        "workflow": workflow,
        "dry_run": True,
        "side_effects": "none; this script does not download, execute shell commands, or create files",
        "base_data_dir": args.base_data_dir,
        "params_dir": args.params_dir,
        "assets": [asdict(asset) for asset in assets],
        "warnings": warnings,
        "next_steps": [
            "Review storage, license, and network requirements before running any equivalent download command.",
            "Validate the target environment with check_openfold_environment.py after installation.",
            "Route command construction to inference/training sub-skills after assets are available.",
        ],
    }


def print_text(plan: dict[str, Any]) -> None:
    print(f"OpenFold asset plan for workflow: {plan['workflow']}")
    print("Mode: dry-run only; no commands are executed and no files are created.")
    for warning in plan["warnings"]:
        print(f"WARNING: {warning}")
    print()

    for index, asset in enumerate(plan["assets"], 1):
        print(f"{index}. {asset['name']}")
        print(f"   Required for: {asset['required_for']}")
        print(f"   Destination: {asset['destination']}")
        print("   Expected paths:")
        for path in asset["expected_paths"]:
            print(f"     - {path}")
        print("   Prerequisites:")
        for prereq in asset["prerequisites"]:
            print(f"     - {prereq}")
        print("   Retrieval notes to convert into approved user-run commands:")
        for note in asset["retrieval_notes"]:
            print(f"     - {note}")
        if asset["notes"]:
            print("   Notes:")
            for note in asset["notes"]:
                print(f"     - {note}")
        print()

    print("Next steps:")
    for step in plan["next_steps"]:
        print(f"- {step}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a dry-run OpenFold parameter/database asset plan without downloading anything.")
    parser.add_argument("--workflow", choices=["monomer", "multimer", "soloseq", "training", "all"], required=True, help="Workflow to plan assets for.")
    parser.add_argument("--base-data-dir", default="data", help="Placeholder base directory for sequence/template/training databases in printed plans.")
    parser.add_argument("--params-dir", default="openfold/resources", help="Placeholder destination for model parameters in printed plans.")
    parser.add_argument("--parameter-set", choices=["auto", "alphafold", "openfold", "both"], default="auto", help="Which parameter families to include when the workflow allows choices.")
    parser.add_argument("--small-bfd", action="store_true", help="Plan Small BFD instead of full BFD for monomer-style database requirements.")
    parser.add_argument("--precomputed-alignments", action="store_true", help="Assume monomer/multimer alignments already exist and omit MSA database downloads from the plan.")
    parser.add_argument("--include-templates", action="store_true", help="For SoloSeq, include optional template-search database assets.")
    parser.add_argument("--json", action="store_true", help="Emit the plan as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan(args)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
