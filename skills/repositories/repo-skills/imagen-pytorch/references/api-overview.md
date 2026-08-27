# API Overview

## Purpose

Use this page when you need a fast, verified map from a public symbol to the module that owns it and the sub-skill that explains it in detail.

## Verified public surface

| Symbol / entry point | Owning module | Typical use | Start here |
| --- | --- | --- | --- |
| `Unet`, `NullUnet`, `BaseUnet64`, `SRUnet256`, `SRUnet1024`, `Imagen` | `imagen_pytorch.imagen_pytorch` | Text-conditioned or unconditional image diffusion, cascade construction, image sampling, and forward training calls | [image-generation](../sub-skills/image-generation/SKILL.md) |
| `ElucidatedImagen` | `imagen_pytorch.elucidated_imagen` | Karras-style / elucidated diffusion image workflows | [image-generation](../sub-skills/image-generation/SKILL.md) |
| `ImagenTrainer` | `imagen_pytorch.trainer` | Dataloaders, EMA, train/valid steps, save/load, resume | [training-and-checkpointing](../sub-skills/training-and-checkpointing/SKILL.md) |
| `UnetConfig`, `ImagenConfig`, `ElucidatedImagenConfig`, `ImagenTrainerConfig` | `imagen_pytorch.configs` | Config-driven model and trainer construction | [configuration-and-cli](../sub-skills/configuration-and-cli/SKILL.md) |
| `Dataset`, `Collator`, `get_images_dataloader` | `imagen_pytorch.data` | Local image folders, URL/image/text rows, and image-only or text-conditioned batches | [data-and-text-conditioning](../sub-skills/data-and-text-conditioning/SKILL.md) |
| `t5_encode_text`, `t5_encode_tokenized_text`, `get_encoded_dim`, `DEFAULT_T5_NAME` | `imagen_pytorch.t5` | Text tokenization / encoding and embed-dimension checks | [data-and-text-conditioning](../sub-skills/data-and-text-conditioning/SKILL.md) |
| `load_imagen_from_checkpoint` | `imagen_pytorch.utils` | Rebuild a commandable Imagen checkpoint and optionally load EMA weights | [training-and-checkpointing](../sub-skills/training-and-checkpointing/SKILL.md) |
| `Unet3D` | `imagen_pytorch.imagen_video` | Video diffusion and video-conditioned cascades | [video-and-inpainting](../sub-skills/video-and-inpainting/SKILL.md) |
| `imagen` console script | `imagen_pytorch.cli` | `config`, `train`, and `sample` commands | [configuration-and-cli](../sub-skills/configuration-and-cli/SKILL.md) |

## Key routing facts

- `imagen_pytorch.__init__` exports the main image, trainer, config, checkpoint, and video symbols listed above.
- `Unet3DConfig` and `NullUnetConfig` live in `imagen_pytorch.configs`; they are not exported from the package root.
- `imagen_pytorch.cli.main()` is a no-op stub; the public CLI surface is the `imagen` Click group.
- `load_imagen_from_checkpoint` expects checkpoint files saved by the package's trainer path with the metadata needed to reconstruct the model.
- The public T5 helpers can trigger Hugging Face downloads or cache access when asked to tokenize raw text. Use the data/text sub-skill when that matters.

## Minimal verified signatures

The installed package inspection confirmed the following signature families:

- `Imagen(unets, *, image_sizes, text_encoder_name='google/t5-v1_1-base', text_embed_dim=None, channels=3, timesteps=1000, cond_drop_prob=0.1, ...)`
- `ElucidatedImagen(unets, *, image_sizes, text_encoder_name='google/t5-v1_1-base', text_embed_dim=None, channels=3, cond_drop_prob=0.1, ..., num_sample_steps=32, sigma_min=0.002, sigma_max=80, ...)`
- `ImagenTrainer(imagen=None, imagen_checkpoint_path=None, use_ema=True, lr=1e-4, eps=1e-8, ..., checkpoint_path=None, checkpoint_every=None, ...)`
- `Dataset(folder, image_size, exts=['jpg', 'jpeg', 'png', 'tiff'], convert_image_to_type=None)`
- `Collator(image_size, url_label, text_label, image_label, name, channels)`
- `Unet3D(*, dim, text_embed_dim=768, ..., temporal_strides=1, ..., resize_mode='nearest')`

Treat the sub-skill references as the place for exact parameter notes, assertions, and workflow recipes.
