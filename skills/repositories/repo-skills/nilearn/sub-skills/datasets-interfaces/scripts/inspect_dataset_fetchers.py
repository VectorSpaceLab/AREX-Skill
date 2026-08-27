#!/usr/bin/env python3
"""Inspect Nilearn dataset/interface entry points without downloads."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from collections.abc import Callable
from typing import Any

SAFE_LOCAL_LOADERS = (
    "load_mni152_template",
    "load_mni152_brain_mask",
    "load_mni152_gm_template",
    "load_mni152_wm_template",
    "load_mni152_gm_mask",
    "load_mni152_wm_mask",
    "load_sample_motor_activation_image",
    "fetch_surf_fsaverage",
    "load_fsaverage",
    "load_fsaverage_data",
)

STATIC_DATASET_SIGNATURES = {
    "fetch_abide_pcp": "(data_dir=None, n_subjects=None, pipeline='cpac', band_pass_filtering=False, global_signal_regression=False, derivatives=None, quality_checked=True, url=None, verbose=1, **kwargs)",
    "fetch_adhd": "(n_subjects=30, data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_atlas_aal": "(version='3v2', data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_atlas_allen_2011": "(data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_atlas_basc_multiscale_2015": "(data_dir=None, url=None, resume=True, verbose=1, resolution=7, version='sym')",
    "fetch_atlas_craddock_2012": "(data_dir=None, url=None, resume=True, verbose=1, homogeneity='spatial', grp_mean=True)",
    "fetch_atlas_destrieux_2009": "(lateralized=True, data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_atlas_difumo": "(dimension=64, resolution_mm=2, data_dir=None, resume=True, verbose=1)",
    "fetch_atlas_harvard_oxford": "(atlas_name, data_dir=None, symmetric_split=False, resume=True, verbose=1)",
    "fetch_atlas_juelich": "(atlas_name, data_dir=None, symmetric_split=False, resume=True, verbose=1)",
    "fetch_atlas_msdl": "(data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_atlas_pauli_2017": "(atlas_type='probabilistic', data_dir=None, verbose=1)",
    "fetch_atlas_schaefer_2018": "(n_rois=400, yeo_networks=7, resolution_mm=1, data_dir=None, base_url=None, resume=True, verbose=1)",
    "fetch_atlas_smith_2009": "(data_dir=None, url=None, resume=True, verbose=1, mirror='origin', dimension=10, resting=True)",
    "fetch_atlas_surf_destrieux": "(data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_atlas_talairach": "(level_name, data_dir=None, verbose=1)",
    "fetch_atlas_yeo_2011": "(data_dir=None, url=None, resume=True, verbose=1, n_networks=7, thickness='thick')",
    "fetch_coords_dosenbach_2010": "(ordered_regions=True)",
    "fetch_coords_power_2011": "()",
    "fetch_coords_seitzman_2018": "(ordered_regions=True)",
    "fetch_development_fmri": "(n_subjects=None, reduce_confounds=True, data_dir=None, resume=True, verbose=1, age_group='both')",
    "fetch_ds000030_urls": "(data_dir=None, verbose=1)",
    "fetch_fiac_first_level": "(data_dir=None, verbose=1)",
    "fetch_haxby": "(data_dir=None, subjects=(2,), fetch_stimuli=False, url=None, resume=True, verbose=1)",
    "fetch_icbm152_2009": "(data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_icbm152_brain_gm_mask": "(data_dir=None, threshold=0.2, resume=True, n_iter=2, verbose=1)",
    "fetch_language_localizer_demo_dataset": "(data_dir=None, verbose=1)",
    "fetch_localizer_button_task": "(data_dir=None, verbose=1)",
    "fetch_localizer_calculation_task": "(n_subjects=1, data_dir=None, verbose=1)",
    "fetch_localizer_contrasts": "(contrasts, n_subjects=None, get_tmaps=False, get_masks=False, get_anats=False, data_dir=None, resume=True, verbose=1)",
    "fetch_localizer_first_level": "(data_dir=None, verbose=1)",
    "fetch_megatrawls_netmats": "(dimensionality=100, timeseries='eigen_regression', matrices='partial_correlation', data_dir=None, resume=True, verbose=1)",
    "fetch_mixed_gambles": "(n_subjects=1, data_dir=None, url=None, resume=True, return_raw_data=False, verbose=1)",
    "fetch_miyawaki2008": "(data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_neurovault": "(max_images=100, collection_terms=None, collection_filter=None, image_terms=None, image_filter=None, data_dir=None, mode='download_new', fetch_neurosynth_words=False, vectorize_words=True, verbose=3, **kwarg_image_filters)",
    "fetch_neurovault_auditory_computation_task": "(data_dir=None, verbose=1, timeout=10.0)",
    "fetch_neurovault_ids": "(image_ids=None, collection_ids=None, data_dir=None, mode='download_new', fetch_neurosynth_words=False, vectorize_words=True, verbose=3, timeout=10.0)",
    "fetch_oasis_vbm": "(n_subjects=None, dartel_version=True, data_dir=None, url=None, resume=True, verbose=1)",
    "fetch_openneuro_dataset": "(urls=None, data_dir=None, dataset_version='ds000030_R1.0.4', verbose=1)",
    "fetch_spm_auditory": "(data_dir=None, data_name='spm_auditory', verbose=1)",
    "fetch_spm_multimodal_fmri": "(data_dir=None, data_name='spm_multimodal_fmri', verbose=1)",
    "fetch_surf_fsaverage": "(mesh='fsaverage5', data_dir=None)",
    "fetch_surf_nki_enhanced": "(n_subjects=10, data_dir=None, url=None, resume=True, verbose=1)",
    "get_data_dirs": "(data_dir=None)",
    "load_fsaverage": "(mesh='fsaverage5', data_dir=None)",
    "load_fsaverage_data": "(mesh='fsaverage5', mesh_type='pial', data_type='sulcal', data_dir=None)",
    "load_mni152_brain_mask": "(resolution=None, threshold=0.2)",
    "load_mni152_gm_mask": "(resolution=None, threshold=0.2, n_iter=2)",
    "load_mni152_gm_template": "(resolution=None)",
    "load_mni152_template": "(resolution=None)",
    "load_mni152_wm_mask": "(resolution=None, threshold=0.2, n_iter=2)",
    "load_mni152_wm_template": "(resolution=None)",
    "load_nki": "(mesh='fsaverage5', mesh_type='pial', n_subjects=1, data_dir=None, url=None, resume=True, verbose=1)",
    "load_sample_motor_activation_image": "()",
    "patch_openneuro_dataset": "(file_list)",
    "select_from_index": "(urls, inclusion_filters=None, exclusion_filters=None, n_subjects=None)",
}

STATIC_INTERFACES = {
    "nilearn.interfaces.bids": {
        "get_bids_files": "(main_path, file_tag='*', file_type='*', sub_label='*', modality_folder='*', filters=None, sub_folder=True)",
        "parse_bids_filename": "(img_path)",
        "save_glm_to_bids": "(*args, **kwargs)",
    },
    "nilearn.interfaces.fmriprep": {
        "load_confounds": "(img_files, strategy=('motion', 'high_pass', 'wm_csf'), motion='full', scrub=5, fd_threshold=0.5, std_dvars_threshold=1.5, wm_csf='basic', global_signal='basic', compcor='anat_combined', n_compcor='all', ica_aroma='full', tedana='aggressive', demean=True)",
        "load_confounds_strategy": "(img_files, denoise_strategy='simple', **kwargs)",
    },
    "nilearn.interfaces.fsl": {
        "get_design_from_fslmat": "(fsl_design_matrix_path, column_names=None)",
    },
}


def _public_callables(module: Any) -> list[str]:
    names = getattr(module, "__all__", None) or [
        name for name in dir(module) if not name.startswith("_")
    ]
    return sorted(
        name for name in names if callable(getattr(module, name, None))
    )


def _signature(obj: Callable[..., Any]) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(...)"


def _describe_result(value: Any) -> dict[str, Any]:
    info: dict[str, Any] = {"type": type(value).__name__}
    shape = getattr(value, "shape", None)
    if shape is not None:
        info["shape"] = list(shape)
    keys = getattr(value, "keys", None)
    if callable(keys):
        info["keys"] = sorted(str(key) for key in keys())
    return info


def _exercise_loader(name: str, func: Callable[..., Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if name.startswith("load_mni152_"):
        kwargs["resolution"] = 2
    if name in {
        "fetch_surf_fsaverage",
        "load_fsaverage",
        "load_fsaverage_data",
    }:
        kwargs["mesh"] = "fsaverage5"
    value = func(**kwargs)
    return {"ok": True, "kwargs": kwargs, "result": _describe_result(value)}


def _static_report(import_error: str | None = None) -> dict[str, Any]:
    dataset_names = sorted(STATIC_DATASET_SIGNATURES)
    return {
        "inventory_source": "bundled-static",
        "import_error": import_error,
        "nilearn_version": "unavailable",
        "datasets": {
            "local_loaders": [
                name for name in dataset_names if name.startswith("load_")
            ],
            "fetchers": [
                name for name in dataset_names if name.startswith("fetch_")
            ],
            "other_helpers": [
                name
                for name in dataset_names
                if not name.startswith(("fetch_", "load_"))
            ],
            "signatures": STATIC_DATASET_SIGNATURES,
        },
        "interfaces": {
            module_name: {
                "callables": sorted(signatures),
                "signatures": signatures,
            }
            for module_name, signatures in STATIC_INTERFACES.items()
        },
        "safe_loader_checks": {
            name: {
                "ok": False,
                "error": "skipped because Nilearn could not be imported",
            }
            for name in SAFE_LOCAL_LOADERS
        },
    }


def build_report(exercise_safe_loaders: bool) -> dict[str, Any]:
    try:
        import nilearn
        import nilearn.datasets as datasets
    except Exception as exc:  # noqa: BLE001
        return _static_report(f"{type(exc).__name__}: {exc}")

    dataset_names = _public_callables(datasets)
    report: dict[str, Any] = {
        "inventory_source": "installed-import",
        "import_error": None,
        "nilearn_version": getattr(nilearn, "__version__", "unknown"),
        "datasets": {
            "local_loaders": [
                name for name in dataset_names if name.startswith("load_")
            ],
            "fetchers": [
                name for name in dataset_names if name.startswith("fetch_")
            ],
            "other_helpers": [
                name
                for name in dataset_names
                if not name.startswith(("fetch_", "load_"))
            ],
            "signatures": {
                name: _signature(getattr(datasets, name))
                for name in dataset_names
            },
        },
        "interfaces": {},
        "safe_loader_checks": {},
    }

    for module_name in STATIC_INTERFACES:
        try:
            module = importlib.import_module(module_name)
            names = _public_callables(module)
            signatures = {
                name: _signature(getattr(module, name)) for name in names
            }
        except Exception as exc:  # noqa: BLE001
            names = sorted(STATIC_INTERFACES[module_name])
            signatures = STATIC_INTERFACES[module_name]
            report.setdefault("interface_import_errors", {})[module_name] = (
                f"{type(exc).__name__}: {exc}"
            )
        report["interfaces"][module_name] = {
            "callables": names,
            "signatures": signatures,
        }

    if exercise_safe_loaders:
        for name in SAFE_LOCAL_LOADERS:
            func = getattr(datasets, name, None)
            if not callable(func):
                report["safe_loader_checks"][name] = {
                    "ok": False,
                    "error": "not available",
                }
                continue
            try:
                report["safe_loader_checks"][name] = _exercise_loader(
                    name, func
                )
            except Exception as exc:  # noqa: BLE001
                report["safe_loader_checks"][name] = {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List Nilearn dataset/interface entry points and optionally "
            "exercise only bundled no-download loaders. No network fetchers "
            "are called."
        )
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        default=True,
        help="Kept for explicitness; network fetchers are never exercised.",
    )
    parser.add_argument(
        "--skip-safe-loaders",
        action="store_true",
        help="Only list APIs; do not call local MNI/fsaverage loaders.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a compact text summary.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(exercise_safe_loaders=not args.skip_safe_loaders)

    if args.json:
        print(json.dumps({"ok": True, **report}, indent=2, sort_keys=True))
        return 0

    print(f"Inventory source: {report['inventory_source']}")
    if report.get("import_error"):
        print(f"Import warning: {report['import_error']}")
    print(f"Nilearn version: {report['nilearn_version']}")
    datasets = report["datasets"]
    print(f"Dataset fetchers: {len(datasets['fetchers'])}")
    print("  " + ", ".join(datasets["fetchers"]))
    print(f"Dataset local loaders: {len(datasets['local_loaders'])}")
    print("  " + ", ".join(datasets["local_loaders"]))
    print("Dataset helper APIs:")
    print("  " + ", ".join(datasets["other_helpers"]))
    print("Interfaces:")
    for module_name, module_report in report["interfaces"].items():
        print(f"  {module_name}: {', '.join(module_report['callables'])}")
    if report["safe_loader_checks"]:
        print("Safe local loader checks:")
        for name, result in report["safe_loader_checks"].items():
            status = "ok" if result.get("ok") else "skipped/failed"
            detail = result.get("result") or result.get("error")
            print(f"  {name}: {status} {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
