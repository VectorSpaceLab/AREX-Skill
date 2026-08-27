#!/usr/bin/env python3
"""Plan a safe Papers-in-100-Lines catalog run/adaptation from a bundled JSON index.

This helper is intentionally stdlib-only. It reads a generated implementation
index, searches for a paper/folder/alias/script query, and prints a conservative
plan. It does not import the original repository, download data, or execute paper
implementation scripts.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

CATEGORY_OWNER = {
    "gan-image-translation": "generative-models",
    "probabilistic-flows-vaes": "generative-models",
    "diffusion-generative-sampling": "generative-models",
    "neural-rendering-3d": "neural-rendering-3d",
    "implicit-representations": "neural-rendering-3d",
    "layers-optimizers": "optimization-meta-rl",
    "meta-learning-hyperopt": "optimization-meta-rl",
    "reinforcement-learning": "optimization-meta-rl",
}

DIRECTORY_OWNER = {
    '3D_Gaussian_Splatting_for_Real_Time_Radiance_Field_Rendering': 'neural-rendering-3d',
    'A_Pixel_Is_Worth_More_Than_One_3D_Gaussians_in_Single_View_3D_Reconstruction': 'neural-rendering-3d',
    'Adam_a_Method_For_Stochastic_Optimization': 'optimization-meta-rl',
    'Adversarial_Feature_Learning': 'generative-models',
    'Adversarially_Learned_Inference': 'generative-models',
    'Auto_Encoding_Variational_Bayes': 'generative-models',
    'Conditional_Generative_Adversarial_Nets': 'generative-models',
    'DPM_Solver_A_Fast_ODE_Solver_for_Diffusion_Probabilistic_Model_Sampling_in_Around_10_Steps': 'generative-models',
    'Deep_Image_Prior': 'optimization-meta-rl',
    'Deep_Reinforcement_Learning_with_Double_Q_learning': 'optimization-meta-rl',
    'Deep_Unsupervised_Learning_using_Nonequilibrium_Thermodynamics': 'generative-models',
    'Denoising_Diffusion_Implicit_Models': 'generative-models',
    'Denoising_Diffusion_Probabilistic_Models': 'generative-models',
    'Density_Estimation_Using_Real_NVP': 'generative-models',
    'DreamBooth_Fine_Tuning_Text_to_Image_Diffusion_Models_for_Subject_Driven_Generation': 'generative-models',
    'FastNeRF_High_Fidelity_Neural_Rendering_at_200FPS': 'neural-rendering-3d',
    'Fast_and_Accurate_Deep_Network_Learning_by_Exponential_Linear_Units_ELUs': 'optimization-meta-rl',
    'Flow_Straight_and_Fast_Learning_to_Generate_and_Transfer_Data_with_Rectified_Flow': 'generative-models',
    'Fourier_Features_Let_Networks_Learn_High_Frequency_Functions_in_Low_Dimensional_Domains': 'neural-rendering-3d',
    'FreeNeRF_Improving_Few_shot_Neural_Rendering_with_Free_Frequency_Regularization': 'neural-rendering-3d',
    'Gaussian_Error_Linear_Units_GELUs': 'optimization-meta-rl',
    'Generative_Adversarial_Networks': 'generative-models',
    'Gromov_Wasserstein_Distances_between_Gaussian_Distributions': 'generative-models',
    'High_Resolution_Image_Synthesis_with_Latent_Diffusion_Models': 'generative-models',
    'Human_level_control_through_deep_reinforcement_learning': 'optimization-meta-rl',
    'Image_to_Image_Translation_with_Conditional_Adversarial_Nets': 'generative-models',
    'Implicit_Neural_Representations_with_Periodic_Activation_Functions': 'neural-rendering-3d',
    'Improved_Techniques_for_Training_GANs': 'generative-models',
    'Improved_Training_of_Wasserstein_GANs': 'generative-models',
    'InfoNeRF_Ray_Entropy_Minimization_for_Few_Shot_Neural_Volume_Rendering': 'neural-rendering-3d',
    'Instant_Neural_Graphics_Primitives_with_a_Multiresolution_Hash_Encoding': 'neural-rendering-3d',
    'KPlanes_Explicit_Radiance_Fields_in_Space_Time_and_Appearance': 'neural-rendering-3d',
    'KiloNeRF_Speeding_up_Neural_Radiance_Fields_with_Thousands_of_Tiny_MLPs': 'neural-rendering-3d',
    'Learned_Initializations_for_Optimizing_Coordinate_Based_Neural_Representations': 'optimization-meta-rl',
    'Least_Squares_Generative_Adversarial_Networks': 'generative-models',
    'Light_Field_Networks_Neural_Scene_Representations_with_Single_Evaluation_Rendering': 'neural-rendering-3d',
    'Likelihood_free_MCMC_with_Amortized_Approximate_Ratio_Estimators': 'generative-models',
    'Masked_Autoregressive_Flow_for_Density_Estimation': 'generative-models',
    'Maxout_Networks': 'optimization-meta-rl',
    'Model_Agnostic_Meta_Learning_for_Fast_Adaptation_of_Deep_Networks': 'optimization-meta-rl',
    'Multiplicative_Filter_Networks': 'neural-rendering-3d',
    'NICE_Non_linear_Independent_Components_Estimation': 'generative-models',
    'NeRF_Representing_Scenes_as_Neural_Radiance_Fields_for_View_Synthesis': 'neural-rendering-3d',
    'Network_In_Network': 'optimization-meta-rl',
    'Neural_Radiance_Fields_Without_Known_Camera_Parameters': 'neural-rendering-3d',
    'On_First_Order_Meta_Learning_Algorithms': 'optimization-meta-rl',
    'On_the_Variance_of_the_Adaptive_Learning_Rate_and_Beyond': 'optimization-meta-rl',
    'Optimizing_Millions_of_Hyperparameters_by_Implicit_Differentiation': 'optimization-meta-rl',
    'Playing_Atari_with_Deep_Reinforcement_Learning': 'optimization-meta-rl',
    'PlenOctrees_for_Real_time_Rendering_of_Neural_Radiance_Fields': 'neural-rendering-3d',
    'Plenoxels_Radiance_Fields_without_Neural_Networks': 'neural-rendering-3d',
    'Proximal_Policy_Optimization_Algorithms': 'optimization-meta-rl',
    'Pseudo_Numerical_Methods_for_Diffusion_Models_on_Manifolds': 'generative-models',
    'Self_Normalizing_Neural_Networks': 'optimization-meta-rl',
    'Sequential_Neural_Likelihood': 'generative-models',
    'Speedy_Splat_Fast_3D_Gaussian_Splatting_with_Sparse_Pixels_and_Sparse_Primitives': 'neural-rendering-3d',
    'Spherical_Voronoi_Directional_Appearance_as_a_Differentiable_Partition_of_the_Sphere': 'neural-rendering-3d',
    'Splatter_Image_Ultra_Fast_Single_View_3D_Reconstruction': 'neural-rendering-3d',
    'Unpaired_Image_to_Image_Translation_using_Cycle_Consistent_Adversarial_Networks': 'generative-models',
    'Unsupervised_Representation_Learning_with_Deep_Convolutional_Generative_Adversarial_Networks': 'generative-models',
    'Variational_Inference_with_Normalizing_Flows': 'generative-models',
    'Wasserstein_GAN': 'generative-models',
}

DIRECTORY_ALIASES = {
    "High_Resolution_Image_Synthesis_with_Latent_Diffusion_Models": [
        "stable diffusion",
        "stable diffusion v1-5",
        "latent diffusion",
        "text to image",
        "safetensors",
        "transformers",
    ],
    "DreamBooth_Fine_Tuning_Text_to_Image_Diffusion_Models_for_Subject_Driven_Generation": [
        "dreambooth",
        "subject driven generation",
        "fine tuning text to image",
    ],
    "NeRF_Representing_Scenes_as_Neural_Radiance_Fields_for_View_Synthesis": [
        "nerf",
        "base nerf",
        "radiance fields",
        "view synthesis",
    ],
    "3D_Gaussian_Splatting_for_Real_Time_Radiance_Field_Rendering": [
        "3dgs",
        "3d gaussian splatting",
        "gaussian splatting",
    ],
    "Adam_a_Method_For_Stochastic_Optimization": [
        "adam",
        "stochastic optimization",
        "optimizer",
    ],
    "On_the_Variance_of_the_Adaptive_Learning_Rate_and_Beyond": [
        "radam",
        "rectified adam",
        "adaptive learning rate",
    ],
    "Pseudo_Numerical_Methods_for_Diffusion_Models_on_Manifolds": [
        "pndm",
        "pseudo numerical methods",
    ],
    "DPM_Solver_A_Fast_ODE_Solver_for_Diffusion_Probabilistic_Model_Sampling_in_Around_10_Steps": [
        "dpm solver",
        "ode solver diffusion",
    ],
    "Neural_Radiance_Fields_Without_Known_Camera_Parameters": [
        "nerf--",
        "nerf without cameras",
        "unknown camera parameters",
    ],
    "Speedy_Splat_Fast_3D_Gaussian_Splatting_with_Sparse_Pixels_and_Sparse_Primitives": [
        "speedy splat",
        "speedy-splat",
    ],
}


def default_index_path() -> Path:
    # scripts/plan_paper_run.py -> sub-skill root -> skill root/references
    return Path(__file__).resolve().parents[3] / "references" / "implementation-index.json"


def norm(text: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def first(raw: Dict[str, Any], names: Sequence[str], default: Any = None) -> Any:
    for name in names:
        if name in raw and raw[name] not in (None, ""):
            return raw[name]
    return default


def collect_entries(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        raise ValueError("index JSON must be an object or list")
    for key in ("entries", "implementations", "papers", "directories", "items"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    # Accept a dict keyed by folder/id.
    dict_entries = []
    for key, value in data.items():
        if isinstance(value, dict):
            item = dict(value)
            item.setdefault("dir", key)
            dict_entries.append(item)
    if dict_entries:
        return dict_entries
    raise ValueError("index JSON has no entries/implementations/papers/directories list")


def script_names(raw: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for key in ("scripts", "source_scripts", "implementation_scripts", "evidence_scripts"):
        for item in as_list(raw.get(key)):
            if isinstance(item, dict):
                value = first(item, ("name", "path", "file"), "")
            else:
                value = item
            if value:
                names.append(Path(str(value)).name)
    for item in as_list(raw.get("python_files")):
        if isinstance(item, dict):
            value = first(item, ("path", "name", "file"), "")
        else:
            value = item
        if value:
            names.append(Path(str(value)).name)
    return sorted(dict.fromkeys(names))


def requirement_strings(raw: Dict[str, Any]) -> List[str]:
    reqs: List[str] = []
    value = raw.get("requirements")
    if isinstance(value, dict):
        for sub in value.values():
            reqs.extend(str(item) for item in as_list(sub))
    else:
        reqs.extend(str(item) for item in as_list(value))
    return [r for r in reqs if r and r != "None"]


def detect_owner(raw: Dict[str, Any], categories: List[str]) -> str:
    owner = first(raw, ("owner", "detail_route", "detail_owner", "group", "subskill", "skill_owner", "planned_skill_owner"))
    if owner:
        if isinstance(owner, list):
            return str(owner[0]) if owner else "paper-catalog-and-execution"
        return str(owner)
    directory = str(first(raw, ("dir", "directory", "folder", "path", "id"), "")).strip()
    if directory in DIRECTORY_OWNER:
        return DIRECTORY_OWNER[directory]
    for category in categories:
        if category in CATEGORY_OWNER:
            return CATEGORY_OWNER[category]
    return "paper-catalog-and-execution"


def detect_flags(raw: Dict[str, Any]) -> List[str]:
    flags = []
    for key in ("flags", "runtime_flags", "safety", "safety_flags", "safety_class"):
        flags.extend(str(item) for item in as_list(raw.get(key)))
    bool_map = {
        "hardcoded_cuda": "hardcoded_cuda",
        "downloads_or_network": "downloads_or_network",
        "dataset_download": "dataset_download",
        "file_outputs": "file_outputs",
        "top_level_train_or_call": "top_level_train_or_call",
    }
    for key, label in bool_map.items():
        if raw.get(key):
            flags.append(label)
    for item in as_list(raw.get("python_files")):
        if isinstance(item, dict):
            for key, label in bool_map.items():
                if item.get(key):
                    flags.append(label)
    if raw.get("asset_dirs") or raw.get("assets"):
        flags.append("assets_required")
    return sorted(dict.fromkeys(f for f in flags if f and f.lower() != "none"))


def normalize_entry(raw: Dict[str, Any]) -> Dict[str, Any]:
    directory = str(first(raw, ("dir", "directory", "folder", "path", "id"), "")).strip()
    title = str(first(raw, ("title", "paper", "paper_title", "name", "display_title"), "")).strip()
    if not title:
        title = directory.replace("_", " ") or "Untitled entry"
    categories = [str(x) for x in as_list(first(raw, ("categories", "category", "families", "tags"), []))]
    aliases = [str(x) for x in as_list(raw.get("aliases"))]
    aliases.extend(DIRECTORY_ALIASES.get(directory, []))
    aliases.extend([title, directory])
    scripts = script_names(raw)
    reqs = requirement_strings(raw)
    flags = detect_flags(raw)
    assets = [str(x) for x in as_list(first(raw, ("asset_dirs", "assets", "asset_paths"), []))]
    commands = [str(x) for x in as_list(first(raw, ("readme_commands", "commands", "usage_commands"), []))]
    symbols: List[str] = []
    for item in as_list(raw.get("symbols")):
        if isinstance(item, dict) and item.get("name"):
            symbols.append(str(item["name"]))
        elif item:
            symbols.append(str(item))
    for py in as_list(raw.get("python_files")):
        if isinstance(py, dict):
            for sym in as_list(py.get("symbols")):
                if isinstance(sym, dict) and sym.get("name"):
                    symbols.append(str(sym["name"]))
                elif sym:
                    symbols.append(str(sym))
    return {
        "title": title,
        "directory": directory,
        "owner": detect_owner(raw, categories),
        "categories": categories,
        "aliases": sorted(dict.fromkeys(aliases)),
        "scripts": scripts,
        "requirements": reqs,
        "flags": flags,
        "assets": assets,
        "commands": commands,
        "symbols": sorted(dict.fromkeys(symbols))[:12],
        "raw": raw,
    }


def load_index(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [normalize_entry(item) for item in collect_entries(data)]


def score_entry(query: str, entry: Dict[str, Any]) -> Tuple[float, str]:
    q = norm(query)
    if not q:
        return 0.0, "empty query"
    fields: List[Tuple[str, str, float]] = []
    fields.append(("title", entry["title"], 5.0))
    fields.append(("folder", entry["directory"], 4.0))
    for alias in entry["aliases"]:
        fields.append(("alias", alias, 5.5))
    for script in entry["scripts"]:
        fields.append(("script", script, 3.5))
    for cat in entry["categories"]:
        fields.append(("category", cat, 2.0))
    for symbol in entry["symbols"]:
        fields.append(("symbol", symbol, 1.5))

    q_tokens = set(q.split())
    best = 0.0
    reason = "weak fuzzy match"
    for label, text, weight in fields:
        t = norm(text)
        if not t:
            continue
        if q == t:
            candidate = 100.0 * weight
            why = f"exact {label} match"
        elif q in t:
            candidate = 50.0 * weight + len(q) / max(len(t), 1)
            why = f"query appears in {label}"
        elif t in q:
            candidate = 42.0 * weight + len(t) / max(len(q), 1)
            why = f"{label} appears in query"
        else:
            t_tokens = set(t.split())
            overlap = len(q_tokens & t_tokens)
            ratio = difflib.SequenceMatcher(None, q, t).ratio()
            candidate = (overlap * 12.0 + ratio * 10.0) * weight
            why = f"token/fuzzy {label} match"
        if candidate > best:
            best = candidate
            reason = why
    return best, reason


def format_list(items: Sequence[str], limit: int = 8, empty: str = "none cataloged") -> str:
    values = [str(x) for x in items if str(x)]
    if not values:
        return empty
    suffix = "" if len(values) <= limit else f" (+{len(values) - limit} more)"
    return ", ".join(values[:limit]) + suffix


def requirement_bases(reqs: Sequence[str]) -> str:
    bases = []
    for req in reqs:
        base = re.split(r"[<>=!~\[]", req)[0].strip()
        if base:
            bases.append(base)
    return format_list(sorted(dict.fromkeys(bases)), limit=10, empty="none listed")


def safety_notes(entry: Dict[str, Any]) -> List[str]:
    text = " ".join([entry["title"], entry["directory"], " ".join(entry["requirements"]), " ".join(entry["flags"])]).lower()
    notes = []
    flags = set(entry["flags"])
    if any(flag in flags for flag in ("hardcoded_cuda", "cuda", "skip-gpu-or-hardware")) or "cuda" in text:
        notes.append("CUDA/device risk: verify hardware and rewrite device handling before any run; CPU substitution is not automatically valid.")
    if any(flag in flags for flag in ("downloads_or_network", "dataset_download", "download", "skip-network")):
        notes.append("Download risk: require explicit approval and pre-supplied data/weights/tokenizers before imports or execution.")
    if "file_outputs" in flags or "writes" in flags:
        notes.append("Output risk: choose/create user-approved output directories before any bounded run.")
    if "assets_required" in flags or entry["assets"]:
        notes.append(f"Asset risk: cataloged assets include {format_list(entry['assets'], limit=6)}.")
    if "top_level_train_or_call" in flags or "skip-expensive" in flags:
        notes.append("Long-loop risk: avoid top-level execution; adapt a tiny controlled snippet with explicit stop limits.")
    if "stable diffusion" in text or "latent diffusion" in text or "safetensors" in text:
        notes.append("Stable Diffusion posture: weights/tokenizer access and realistic inference are resource-heavy; do not auto-download.")
    if "dreambooth" in text or "diffusers" in text:
        notes.append("DreamBooth/Diffusers posture: fine-tuning/inference needs model assets and a deliberate GPU/memory budget.")
    if "nerf" in text or "gaussian splatting" in text or "radiance" in text:
        notes.append("Rendering posture: expect camera/data assets, CUDA pressure, long optimization/rendering, and image outputs.")
    if "adam" in text or "keras" in text:
        notes.append("Optimizer/Keras posture: old Keras/Torch pins and dataset helpers may conflict with modern environments.")
    if "atari" in text or "gym" in text or "stable_baselines3" in text:
        notes.append("RL posture: Gym/ALE/ROM setup and long reward training are outside a lookup smoke test.")
    if not notes:
        notes.append("No special hazards were detected in the catalog fields; still use a no-execution default until the user authorizes a bounded run.")
    return notes


def print_groups(entries: Sequence[Dict[str, Any]]) -> None:
    counts = Counter(entry["owner"] for entry in entries)
    print("Catalog groups:")
    for group, count in sorted(counts.items()):
        print(f"- {group}: {count}")
    print("\nCommon broad queries:")
    print("- generative-models: GAN, VAE, flow, diffusion, DDPM, DDIM, PNDM, DPM-Solver, Stable Diffusion, DreamBooth")
    print("- neural-rendering-3d: NeRF, 3DGS, Gaussian Splatting, Plenoxels, K-Planes, SIREN, LFN, Splatter")
    print("- optimization-meta-rl: Adam, RAdam, ELU, GELU, SELU, Maxout, NiN, MAML, Reptile, DQN, PPO")


def print_plan(query: str, matches: Sequence[Tuple[float, str, Dict[str, Any]]], max_results: int) -> int:
    if not matches or matches[0][0] <= 0:
        print(f"No catalog match for query: {query!r}")
        print("Try --list-groups, a longer paper title, a folder label, or an evidence script label.")
        return 1

    best_score, best_reason, best = matches[0]
    close = [m for m in matches[1:max_results] if m[0] >= best_score * 0.72]

    print(f"Query: {query}")
    print(f"Best match: {best['title']}")
    if best["directory"]:
        print(f"Folder label: {best['directory']} (catalog label only)")
    print(f"Why matched: {best_reason}; score={best_score:.1f}")
    print(f"Detail route: {best['owner']}")
    print(f"Evidence script labels: {format_list(best['scripts'])} (not commands to run)")
    print(f"Requirement bases: {requirement_bases(best['requirements'])}")
    print(f"Safety flags: {format_list(best['flags'], empty='none cataloged')}")
    print(f"Assets: {format_list(best['assets'], empty='none cataloged')}")

    if close:
        print("\nPossible ambiguity:")
        for score, reason, entry in close:
            label = entry["title"]
            folder = f" [{entry['directory']}]" if entry["directory"] else ""
            print(f"- {label}{folder}: route={entry['owner']}, score={score:.1f}, reason={reason}")
        print("If the user's intent depends on the exact paper, ask them to choose before planning execution.")

    print("\nConservative safe plan:")
    print("1. Treat this as lookup/adaptation planning only; do not run upstream implementation scripts from the catalog.")
    print("2. If algorithm details are needed, load the detail route above after this catalog selection.")
    print("3. Use an isolated environment for this single entry only; do not combine requirements across paper folders.")
    print("4. Before any user-approved bounded run, check device, data/weights/tokenizers, output directories, and stop limits.")
    print("5. For adaptation, rewrite the minimal needed pattern with explicit data, device, output path, and iteration limits.")

    print("\nHazards to mention:")
    for note in safety_notes(best):
        print(f"- {note}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search the bundled Papers-in-100-Lines implementation index and print a conservative run/adaptation plan.",
    )
    parser.add_argument(
        "--index-json",
        type=Path,
        default=default_index_path(),
        help="Path to implementation-index.json (default: skill-root references/implementation-index.json).",
    )
    parser.add_argument("--query", "-q", help="Paper title, alias, folder label, script label, or concept to search for.")
    parser.add_argument("--list-groups", action="store_true", help="List catalog group counts and broad query hints.")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum close matches to display for ambiguity (default: 5).")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.list_groups and not args.query:
        parser.error("provide --query or --list-groups")

    try:
        entries = load_index(args.index_json)
    except FileNotFoundError:
        print(f"Index JSON not found: {args.index_json}", file=sys.stderr)
        print("Provide --index-json or ensure ../../references/implementation-index.json exists in the generated skill.", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Could not read implementation index: {exc}", file=sys.stderr)
        return 2

    if args.list_groups:
        print_groups(entries)
        if not args.query:
            return 0
        print()

    matches = []
    assert args.query is not None
    for entry in entries:
        score, reason = score_entry(args.query, entry)
        matches.append((score, reason, entry))
    matches.sort(key=lambda item: item[0], reverse=True)
    return print_plan(args.query, matches, max(1, args.max_results))


if __name__ == "__main__":
    raise SystemExit(main())
