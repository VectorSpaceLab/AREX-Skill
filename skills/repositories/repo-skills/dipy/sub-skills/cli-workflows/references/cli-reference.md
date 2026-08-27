# Dipy CLI Reference

Dipy console commands are declared as project scripts and dispatch through `dipy.workflows.cli:run`. The current inspected runtime exposes 61 flows in `dipy.workflows.cli.cli_flows`, where each mapping value is a `(module_name, class_name)` tuple. Treat this catalog as command discovery and workflow routing guidance; route scientific parameter interpretation to the owning Dipy sub-skill.

## Command Families

| Family | Commands | Owns | Route deeper science to |
| --- | ---: | --- | --- |
| `align` | 7 | image registration, transforms, motion correction, reslice, SLR, BundleWarp | `registration-alignment` |
| `denoise` | 5 | LPCA, MPPCA, NLMeans, Patch2Self, Gibbs ringing removal | `denoising-preprocessing` |
| `io` | 15 | fetch/info/extract/split/math/conversion/PAM/tractogram utilities | `io-data` |
| `mask` | 1 | threshold mask command | `denoising-preprocessing` or `tracking-segmentation` by use case |
| `nn` | 2 | optional neural-network correction/extraction commands | `denoising-preprocessing`; optional backend caveats here |
| `reconst` | 18 | reconstruction model CLIs | `reconstruction-models` |
| `segment` | 6 | brain mask, tissue classification, clustering, RecoBundles/LabelsBundles | `tracking-segmentation` |
| `stats` | 4 | BUAN, tractometry, SNR in corpus callosum | `tracking-segmentation` or stats owner if present |
| `tracking` | 2 | local tracking and PFT workflows | `tracking-segmentation` |
| `viz` | 1 | Horizon visualization | optional visualization caveats here; science routes by data type |

## Alignment And Registration Commands

| Command | Workflow class | Use for | Notes |
| --- | --- | --- | --- |
| `dipy_align_affine` | `ImageRegistrationFlow` | center-of-mass, translation, rigid, affine image registration | Use `--help` to inspect transform options; deeper registration strategy belongs to `registration-alignment`. |
| `dipy_align_syn` | `SynRegistrationFlow` | symmetric diffeomorphic registration | Requires image registration inputs and metric choices. |
| `dipy_apply_transform` | `ApplyTransformFlow` | apply a saved affine or diffeomorphic transform | Match transform type to file produced by registration. |
| `dipy_bundlewarp` | `BundleWarpFlow` | nonlinear white-matter bundle registration | Use cautious deformation settings; route anatomical interpretation to `registration-alignment`/`tracking-segmentation`. |
| `dipy_correct_motion` | `MotionCorrectionFlow` | between-volume DWI motion correction | Usually before reconstruction; ensure b-values/b-vectors match the DWI. |
| `dipy_reslice` | `ResliceFlow` | change voxel resolution / resample images | Validate affine and output shape after running. |
| `dipy_slr` | `SlrWithQbxFlow` | streamline-based linear registration | Tractogram space/origin handling belongs to `io-data` and `registration-alignment`. |

## Denoising And Preprocessing Commands

| Command | Workflow class | Use for | Notes |
| --- | --- | --- | --- |
| `dipy_denoise_lpca` | `LPCAFlow` | local PCA denoising with gradient information | Route patch radius, sigma, and gtab details to `denoising-preprocessing`. |
| `dipy_denoise_mppca` | `MPPCAFlow` | Marchenko-Pastur PCA denoising / sigma estimation | Useful when no prior sigma estimate is available. |
| `dipy_denoise_nlmeans` | `NLMeansFlow` | non-local means denoising | Requires sigma and image-dimensionality choices. |
| `dipy_denoise_patch2self` | `Patch2SelfFlow` | self-supervised DWI denoising | Check runtime cost and input dimensionality. |
| `dipy_gibbs_ringing` | `GibbsRingingFlow` | Gibbs ringing suppression | Set process count conservatively on shared machines. |
| `dipy_mask` | `MaskFlow` | threshold a volume into a mask | General utility; route brain-extraction strategy to `tracking-segmentation` or preprocessing owner. |

## IO, Dataset, And Conversion Commands

| Command | Workflow class | Use for | Notes |
| --- | --- | --- | --- |
| `dipy_fetch` | `FetchFlow` | list/fetch Dipy datasets | May use network or local caches depending on arguments; avoid in offline verification unless listing only. |
| `dipy_info` | `IoInfoFlow` | inspect image, bval/bvec, or tractogram metadata | Safe first command for unknown inputs. |
| `dipy_extract_b0` | `ExtractB0Flow` | extract b0 volumes from DWI | Requires matching gradient files. |
| `dipy_extract_shell` | `ExtractShellFlow` | extract a diffusion shell | Validate target b-value tolerance in `io-data`. |
| `dipy_extract_volume` | `ExtractVolumeFlow` | extract volume index from 4D image | Check 0-based volume index in help. |
| `dipy_split` | `SplitFlow` | split 4D image volumes | Use explicit output directory and filenames. |
| `dipy_math` | `MathFlow` | basic math over image files | Confirm operation semantics with `--help`. |
| `dipy_concatenate_tractograms` | `ConcatenateTractogramFlow` | concatenate tractogram files | Validate compatible reference/space assumptions. |
| `dipy_convert_tractogram` | `ConvertTractogramFlow` | convert tractogram formats | Route reference and coordinate-space details to `io-data`. |
| `dipy_convert_tensors` | `ConvertTensorsFlow` | convert tensor representation | Check expected tensor layout before using outputs downstream. |
| `dipy_convert_sh` | `ConvertSHFlow` | convert spherical harmonic conventions | Preferred over deprecated `dipy_sh_convert_mrtrix`. |
| `dipy_sh_convert_mrtrix` | `ConvertSHFlow` | deprecated MRtrix SH conversion alias | Use `dipy_convert_sh` in new instructions. |
| `dipy_nifti2pam` | `NiftisToPamFlow` | package NIfTI-derived reconstruction outputs into PAM | Route PAM schema details to `io-data`/`reconstruction-models`. |
| `dipy_pam2nifti` | `PamToNiftisFlow` | export PAM metrics into NIfTI files | Use explicit output names for reproducibility. |
| `dipy_tensor2pam` | `TensorToPamFlow` | convert tensor output to PAM | Tensor metric meaning belongs to `reconstruction-models`. |

## Reconstruction Commands

| Command | Workflow class | Use for | Notes |
| --- | --- | --- | --- |
| `dipy_fit_dti` | `ReconstDtiFlow` | diffusion tensor fitting and tensor-derived maps | Route metric/model questions to `reconstruction-models`; this sub-skill only owns CLI mechanics. |
| `dipy_fit_csd` | `ReconstCSDFlow` | constrained spherical deconvolution | Requires response/SH/peaks choices. |
| `dipy_fit_msmtcsd` | `ReconstCSDFlow` | multi-shell multi-tissue CSD variant | CLI injects `--use_msmt` default behavior through extra args. |
| `dipy_fit_csa` | `ReconstQBallBaseFlow` | Constant Solid Angle model | CLI injects method `csa`. |
| `dipy_fit_qball` | `ReconstQBallBaseFlow` | Q-ball model | CLI injects method `qball`. |
| `dipy_fit_opdt` | `ReconstQBallBaseFlow` | OPDT model | CLI injects method `opdt`. |
| `dipy_fit_dki` | `ReconstDkiFlow` | diffusion kurtosis imaging | Needs sufficient gradient sampling. |
| `dipy_fit_dsi` | `ReconstDsiFlow` | diffusion spectrum imaging | High-dimensional model; inspect help and data requirements. |
| `dipy_fit_dsid` | `ReconstDsiFlow` | DSI deconvolution variant | CLI injects `--remove_convolution` default behavior through extra args. |
| `dipy_fit_force` | `ReconstForceFlow` | FORECAST/force reconstruction surface | Route model-specific settings to `reconstruction-models`. |
| `dipy_fit_forecast` | `ReconstForecastFlow` | FORECAST model | Route assumptions and outputs to `reconstruction-models`. |
| `dipy_fit_fwdti` | `ReconstFwdtiFlow` | free-water DTI | Check mask and acquisition suitability. |
| `dipy_fit_gqi` | `ReconstGQIFlow` | generalized q-sampling imaging | Route model selection to `reconstruction-models`. |
| `dipy_fit_ivim` | `ReconstIvimFlow` | IVIM model | Requires b-value regime suited to IVIM. |
| `dipy_fit_mapmri` | `ReconstMAPMRIFlow` | MAP-MRI metrics | Needs small/big delta values where required. |
| `dipy_fit_powermap` | `ReconstPowermapFlow` | power map reconstruction | Route scientific interpretation to `reconstruction-models`. |
| `dipy_fit_sdt` | `ReconstSDTFlow` | spherical deconvolution transform | Route response and SH choices to model owner. |
| `dipy_fit_sfm` | `ReconstSFMFlow` | sparse fascicle model | Route model assumptions to `reconstruction-models`. |

## Tracking, Segmentation, And Statistics Commands

| Command | Workflow class | Use for | Notes |
| --- | --- | --- | --- |
| `dipy_track` | `LocalFiberTrackingPAMFlow` | local fiber tracking from PAM/peaks/stopping/seeding data | Route stopping criteria, seeding, and output tractogram validation to `tracking-segmentation`. |
| `dipy_track_pft` | `PFTrackingPAMFlow` | particle filtering tracking | Needs tissue partial-volume maps; route details to `tracking-segmentation`. |
| `dipy_brain_mask` | `BrainMaskFlow` | brain mask extraction | Optional model/dependency surfaces may apply. |
| `dipy_classify_tissue` | `ClassifyTissueFlow` | tissue classification | Route PVE interpretation to `tracking-segmentation`. |
| `dipy_cluster_streamlines` | `ClusterStreamlinesFlow` | streamline clustering | May need plotting dependencies for some outputs; inspect help. |
| `dipy_labelsbundles` | `LabelsBundlesFlow` | label recognized bundles | Route bundle models and tractograms to `tracking-segmentation`. |
| `dipy_median_otsu` | `MedianOtsuFlow` | median Otsu brain extraction | Common preprocessing step before reconstruction. |
| `dipy_recobundles` | `RecoBundlesFlow` | recognize bundles from tractograms | Requires atlas/model bundle organization. |
| `dipy_buan_profiles` | `BundleAnalysisTractometryFlow` | generate BUAN tractometry profiles | Expects BUAN directory structure. |
| `dipy_buan_lmm` | `LinearMixedModelsFlow` | linear mixed models over BUAN profiles | May require plotting/statistics dependencies. |
| `dipy_buan_shapes` | `BundleShapeAnalysis` | bundle shape similarity analysis | Route interpretation to `tracking-segmentation`. |
| `dipy_snr_in_cc` | `SNRinCCFlow` | SNR in corpus callosum | Check required mask/label inputs. |

## Optional Visualization And Neural-Network Commands

| Command | Workflow class | Optional surface | Notes |
| --- | --- | --- | --- |
| `dipy_horizon` | `HorizonFlow` | visualization / GUI | Needs visualization stack such as FURY and a display-capable environment. Base inspection lacked `fury` and `matplotlib`; help may still import before failing on runtime visualization. |
| `dipy_correct_biasfield` | `BiasFieldCorrectionFlow` | neural-network bias correction | Base inspection lacked `torch` and `tensorflow`; treat as optional and verify imports/help before recommending. |
| `dipy_evac_plus` | `EVACPlusFlow` | neural-network extraction/correction workflow | Optional model backend; document missing backend as an environment issue, not a core Dipy CLI failure. |

## API Recipe To CLI Translation

1. Identify the scientific owner first: IO/data, reconstruction, preprocessing, registration, tracking/segmentation, or visualization.
2. Find the closest `dipy_*` command in the family table.
3. Run `COMMAND --help` to inspect the command-specific positional inputs and optional defaults; do not infer all flags from API names.
4. Use the same file contracts as the API recipe: DWI image + bvals/bvecs for many reconstruction/preprocessing flows, tractogram + reference for tractogram conversions, PAM/peaks for tracking.
5. Set `--out_dir` and `out_*` names explicitly when examples will be reused or compared.
6. Preserve `--log_level`, `--log_file`, and `--force` decisions in reproducibility notes.

## CLI To API Translation

1. Map the command to its workflow class using this reference or `scripts/dipy_cli_probe.py`.
2. Inspect `COMMAND --help`; the help table mirrors the workflow `run` docstring and signature.
3. Locate the workflow class under `dipy.workflows.<family>` for command orchestration logic.
4. Route underlying algorithms to the owning sub-skill rather than copying workflow internals into CLI guidance.
5. For reconstruction peaks, use `dipy.direction.peaks.peaks_from_model` in API recipes, not `dipy.reconst.peaks`.
