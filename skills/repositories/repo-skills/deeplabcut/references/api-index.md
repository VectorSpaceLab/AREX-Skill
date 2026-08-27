# DeepLabCut API index

Read this to route a public API or task phrase to the right sub-skill. Signatures are summarized from installed-package inspection of DeepLabCut 3.0.1.

## Project setup and configuration

Owner: [install-and-project-setup](../sub-skills/install-and-project-setup/SKILL.md)

| API | Use for |
| --- | --- |
| `deeplabcut.create_new_project(project, experimenter, videos, working_directory=None, copy_videos=False, video_extensions=None, multianimal=False, individuals=None)` | Create a standard or multi-animal project skeleton with videos and `config.yaml`. |
| `deeplabcut.add_new_videos(config, videos, copy_videos=False, coords=None, extract_frames=False)` | Add videos to an existing project and optionally extract frames. |
| `deeplabcut.create_new_project_3d(project, experimenter, num_cameras=2, working_directory=None)` | Create a 3D project skeleton. |
| `deeplabcut.auxiliaryfunctions` and config helpers | Read/edit project configs and derived paths. |

## Data labeling and trainset creation

Owner: [data-labeling-and-training-datasets](../sub-skills/data-labeling-and-training-datasets/SKILL.md)

| API | Use for |
| --- | --- |
| `deeplabcut.extract_frames(config, mode='automatic', algo='kmeans', crop=False, ...)` | Extract candidate frames for labeling. |
| `deeplabcut.label_frames(config)` and `deeplabcut.refine_labels(config)` | Launch GUI labeling/refinement when GUI dependencies are installed. |
| `deeplabcut.check_labels(config, ...)` | Render/verify labeled frames after annotation or conversion. |
| `deeplabcut.create_training_dataset(config, num_shuffles=1, ..., net_type=None, detector_type=None, augmenter_type=None, weight_init=None, engine=None, ctd_conditions=None)` | Build train/test datasets and shuffles. |
| `deeplabcut.create_training_dataset_from_existing_split(...)` | Reuse train/test indices from an existing shuffle with new model/config choices. |
| `deeplabcut.create_training_model_comparison(...)` | Create comparable shuffles for model/augmentation comparison. |
| `deeplabcut.convertcsv2h5`, `deeplabcut.convert2_maDLC`, `deeplabcut.mergeandsplit` | Convert or normalize annotation datasets. |

## PyTorch training, evaluation, inference, and export

Owner: [pytorch-training-evaluation-inference](../sub-skills/pytorch-training-evaluation-inference/SKILL.md)

| API | Use for |
| --- | --- |
| `deeplabcut.train_network(config, shuffle=1, trainingsetindex=0, epochs=None, save_epochs=None, device=None, snapshot_path=None, detector_path=None, batch_size=None, detector_batch_size=None, pytorch_cfg_updates=None, ...)` | Train or resume a PyTorch shuffle. |
| `deeplabcut.evaluate_network(config, shuffles=(1,), plotting=False, comparison_bodyparts='all', pcutoff=None, engine=None, **torch_kwargs)` | Evaluate one or more snapshots/shuffles. |
| `deeplabcut.analyze_videos(config, videos, video_extensions=None, shuffle=1, save_as_csv=False, destfolder=None, batch_size=None, dynamic=(False, 0.5, 10), auto_track=True, n_tracks=None, animal_names=None, identity_only=False, engine=None, **torch_kwargs)` | Analyze videos and write prediction files. |
| `deeplabcut.analyze_images` and related compatibility APIs | Analyze still images or time-lapse frames. |
| `deeplabcut.export_model(cfg_path, shuffle=1, trainingsetindex=0, snapshotindex=None, overwrite=False, make_tar=True, without_detector=False, engine=None)` | Export model artifacts. |
| `deeplabcut.return_train_network_path` and `deeplabcut.return_evaluate_network_data` | Inspect model/evaluation output paths and data. |

## Multi-animal tracking

Owner: [multi-animal-tracking](../sub-skills/multi-animal-tracking/SKILL.md)

| API | Use for |
| --- | --- |
| `deeplabcut.convert_detections2tracklets(config, videos, video_extensions=None, shuffle=1, overwrite=False, track_method='', identity_only=False, ...)` | Convert raw multi-animal detections into tracklets. |
| `deeplabcut.stitch_tracklets(config_path, videos, video_extensions=None, n_tracks=None, animal_names=None, min_length=10, transformer_checkpoint='', save_as_csv=False, ...)` | Stitch sparse tracklets into full animal tracks. |
| `deeplabcut.transformer_reID(config, videos, track_method='ellipse', n_tracks=None, n_triplets=1000, train_epochs=100, ...)` | Train/use appearance-based re-identification for track stitching. |
| `deeplabcut.create_tracking_dataset` | Prepare tracking datasets used by tracking workflows. |

## Model Zoo and SuperAnimal

Owner: [model-zoo-superanimal](../sub-skills/model-zoo-superanimal/SKILL.md)

| API | Use for |
| --- | --- |
| `deeplabcut.video_inference_superanimal(videos, superanimal_name, model_name, detector_name=None, scale_list=None, video_adapt=False, device='auto', customized_pose_checkpoint=None, customized_detector_checkpoint=None, create_labeled_video=True, ...)` | Run pretrained SuperAnimal video inference or adaptation. |
| `deeplabcut.create_pretrained_project` | Create a project from pretrained weights. |
| `deeplabcut.create_pretrained_human_project` | Legacy human-body pretrained project creation path. |

## Post-processing, 3D, video utilities, and exports

Owner: [postprocessing-3d-video-exports](../sub-skills/postprocessing-3d-video-exports/SKILL.md)

| API | Use for |
| --- | --- |
| `deeplabcut.filterpredictions(config, video, filtertype='median', windowlength=5, save_as_csv=True, ...)` | Smooth/filter analyzed predictions. |
| `deeplabcut.extract_outlier_frames(config, videos, outlieralgorithm='jump', extractionalgorithm='kmeans', ...)` | Extract frames for label refinement based on bad predictions. |
| `deeplabcut.merge_datasets(config, forceiterate=None)` | Merge refined labels and advance iterations. |
| `deeplabcut.create_labeled_video(config, videos, filtered=False, draw_skeleton=False, color_by='bodypart', overwrite=False, ...)` | Render predictions on videos. |
| `deeplabcut.plot_trajectories(config, videos, filtered=False, displayedbodyparts='all', ...)` | Plot trajectories from prediction files. |
| `deeplabcut.CropVideo`, `ShortenVideo`, `DownSampleVideo`, `check_video_integrity` | Basic video utility operations. |
| `deeplabcut.calibrate_cameras`, `check_undistortion`, `triangulate`, `create_labeled_video_3d` | Multi-camera 3D workflows. |
