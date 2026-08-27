# Metrics API Reference

Verified signatures:

- `detection_metrics.get_detection_metric_ops(config, prediction_frame_id, prediction_bbox, prediction_type, prediction_score, prediction_overlap_nlz, ground_truth_frame_id, ground_truth_bbox, ground_truth_type, ground_truth_difficulty, ground_truth_speed=None, recall_at_precision=None, name_filter=None)`
- `tracking_metrics.get_tracking_metric_ops(config, prediction_bbox, prediction_type, prediction_score, prediction_frame_id, prediction_sequence_id, prediction_object_id, ground_truth_bbox, ground_truth_type, ground_truth_frame_id, ground_truth_sequence_id, ground_truth_object_id, ground_truth_difficulty, prediction_overlap_nlz=None, ground_truth_speed=None)`
- `motion_metrics.get_motion_metric_ops(config, prediction_trajectory, prediction_score, ground_truth_trajectory, ground_truth_is_valid, prediction_ground_truth_indices, prediction_ground_truth_indices_mask, object_type, object_id=None, scenario_id=None)`
- `config_util_py.get_breakdown_names_from_config(config)` and `get_breakdown_names_from_motion_config(config)`
- `keypoint_metrics.object_keypoint_similarity(gt, pr, box, per_type_scales, sample_weight=None)`

Detection boxes use 4, 5, or 7 degrees of freedom depending on config box type. Motion metrics require statically known non-batch dimensions for groups, top-K predictions, agents, prediction steps, and ground-truth steps. Most metric wrappers use TensorFlow v1-style local metric variables even under TensorFlow 2.
