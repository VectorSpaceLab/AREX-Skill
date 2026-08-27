# nnU-Net pretrained models

The pretrained-model helpers list built-in TaskXXX model archives, print their
license warning, and can download or install them.

## Public helper commands

- `nnUNet_print_available_pretrained_models`
- `nnUNet_print_pretrained_model_info TASK_NAME`
- `nnUNet_download_pretrained_model TASK_NAME`
- `nnUNet_download_pretrained_model_by_url URL`
- `nnUNet_install_pretrained_model_from_zip ZIP`
- `nnUNet_export_model_to_zip -t TASK -o OUTPUT.zip ...`

## Caution

- Downloading a model may overwrite an existing installation in the trained
  model directory.
- The helpers rely on `requests` for network access.
- Always confirm the dataset license before using a pretrained model.

## Built-in TaskXXX catalog

| Task | Summary | Typical modalities |
| --- | --- | --- |
| `Task001_BrainTumour` | Brain tumor segmentation | FLAIR, T1, T1c, T2 |
| `Task002_Heart` | Left atrium segmentation | MRI |
| `Task003_Liver` | Liver and liver tumor segmentation | CT |
| `Task004_Hippocampus` | Hippocampus segmentation | MRI |
| `Task005_Prostate` | Prostate segmentation | T2, ADC |
| `Task006_Lung` | Lung nodule segmentation | CT |
| `Task007_Pancreas` | Pancreas and pancreas tumor segmentation | CT |
| `Task008_HepaticVessel` | Hepatic vessel and liver tumor segmentation | CT |
| `Task009_Spleen` | Spleen segmentation | CT |
| `Task010_Colon` | Colon cancer segmentation | CT |
| `Task017_AbdominalOrganSegmentation` | Abdomen organ segmentation | CT |
| `Task024_Promise` | Prostate MR image segmentation | T2 |
| `Task027_ACDC` | Cardiac segmentation | cine MRI |
| `Task029_LiTS` | Liver and liver tumor challenge | CT |
| `Task035_ISBILesionSegmentation` | MS lesion segmentation | FLAIR, MPRAGE, PD, T2 |
| `Task038_CHAOS_Task_3_5_Variant2` | Healthy abdominal organ segmentation | T1 in-/out-phase, T2 |
| `Task048_KiTS_clean` | Kidney and kidney tumor segmentation | CT |
| `Task055_SegTHOR` | Thoracic organs at risk | CT |
| `Task061_CREMI` | Synaptic cleft segmentation | electron microscopy |
| `Task075_Fluo_C3DH_A549_ManAndSim` | Cell tracking challenge data | fluorescence microscopy |
| `Task076_Fluo_N3DH_SIM` | Cell border and center segmentation | fluorescence microscopy |
| `Task089_Fluo-N2DH-SIM_thickborder_time` | Time-series cell segmentation | fluorescence microscopy over time |

## When to use which helper

- Use `print_available_pretrained_models` when you need the full catalog.
- Use `print_pretrained_model_info` when you need the input modalities and task
  summary for a specific model.
- Use `download_by_name` only when the user explicitly asked to download a
  model by task name.
- Use `download_by_url` only when the user already has a trusted archive URL.
- Use `install_from_zip_entry_point` when the user already has a zip file.
- Use `export_entry_point` when you want to package an already-trained model for
  sharing.

## Common failure modes

- Missing `RESULTS_FOLDER` prevents installation into the nnU-Net results tree.
- Missing `requests` breaks the download helpers.
- A model archive can overwrite an existing folder with the same trainer and
  plans identifier.
