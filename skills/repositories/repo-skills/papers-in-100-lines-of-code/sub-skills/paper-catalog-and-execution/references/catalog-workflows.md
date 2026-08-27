# Catalog Workflows

This reference is self-contained catalog and planning guidance for all 62 paper entries. It distills the root catalog, per-paper README usage snippets, per-paper requirements, static AST/source inventory, native candidate map, and source-script inventory decisions. It does not require the original repository checkout at runtime.

## Core rule

Use the generated root catalog at `../../references/implementation-index.json` or the table below to choose and plan. Do not launch upstream implementation scripts as part of lookup. Evidence script labels in this reference identify compact implementations from the catalog; they are not runtime dependencies and are not commands to execute.

## Search and selection workflow

1. **Normalize the query.** Lowercase, remove punctuation, and consider folder-style underscores, paper titles, common aliases, and evidence script labels. Important aliases include Stable Diffusion v1-5 -> High-Resolution Image Synthesis with Latent Diffusion Models; NeRF -> NeRF, NeRF--, FastNeRF, KiloNeRF, FreeNeRF, InfoNeRF, PlenOctrees, Plenoxels, and related 3D entries; Adam -> Adam and RAdam.
2. **List candidate groups when broad.** For broad terms such as "diffusion", "GAN", "rendering", "optimizer", or "RL", use `scripts/plan_paper_run.py --list-groups` and then query a narrower title.
3. **Compare evidence, not just titles.** A matching entry should agree on at least two of: title/alias, folder label, evidence script label, requirements, family route, or source safety flags.
4. **Resolve ambiguity explicitly.** If the top choices are close, present two to five alternatives with their sibling route and risk posture. Ask only when the user's intended paper or task would change the plan.
5. **Plan one entry at a time.** Requirements pin old and mutually incompatible package versions. Do not install the combined requirements of multiple paper folders.
6. **Route details after selection.** This sub-skill owns lookup and safety planning. Load the sibling sub-skill for algorithm details, implementation adaptation patterns, tensor shapes, training loops, or rendering/generative/RL-specific troubleshooting.

## Safe run/adaptation planning workflow

Use this sequence for any user request that asks "can I run this?", "what do I need?", or "adapt this 100-line script".

1. **State the requested outcome.** Distinguish lookup, static review, small adaptation, smoke test, inference, training, rendering, fine-tuning, or reproduction.
2. **Summarize catalog facts.** Include title/folder, sibling route, evidence script labels, requirement bases, assets, and risk flags.
3. **Choose a no-execution default.** Unless the user has explicitly authorized a bounded run, produce only a plan. Full native runs are optional/unverified for this skill scope.
4. **Dependency strategy.** Create or use an isolated environment for the selected entry only. Treat `torch==...+cu*`, old Keras/Torch/Torchvision pins, Gym/Stable-Baselines pins, and Diffusers/Transformers/Safetensors as special cases requiring deliberate compatibility checks.
5. **Side-effect audit.** Before any import or execution, check for dataset downloads, `from_pretrained` model/tokenizer access, hard-coded `cuda`, output-directory writes, expected asset folders, and top-level train loops.
6. **Bounded adaptation.** Prefer rewriting the small needed concept into the user's project with explicit device, data, output, and stop controls. If exact source review is needed, use only source material made available for the current task and do not depend on a local checkout path.
7. **Handoff.** Name the sibling route for deeper work and list blockers: missing dataset/weights/assets, unsupported CUDA, incompatible pins, unknown output paths, or long-loop budget.

## Safety labels used here

- **CUDA**: static evidence includes hard-coded CUDA or CUDA-only assumptions. CPU substitution is at best a deliberate adaptation, not verified parity.
- **download**: static evidence or requirements indicate dataset/model/tokenizer/network access risk.
- **writes**: scripts create result images, GIFs, trajectories, checkpoints, or plots; plan output paths before running.
- **assets**: README or inventory references expected local data, images, pretrained weights, camera files, or generated output directories.
- **top-level loop**: code may train or render immediately after import or entrypoint execution and may lack CLI stop controls.

## 62-entry catalog quick reference

| Paper / folder label | Detail route | Evidence script labels | Requirement bases | Safety posture |
|---|---|---|---|---|
| 3D Gaussian Splatting for Real-Time Radiance Field Rendering<br>`3D_Gaussian_Splatting_for_Real_Time_Radiance_Field_Rendering` | neural-rendering-3d | 3dgs.py | torch, numpy, pillow, tqdm | CUDA, assets, writes |
| A Pixel Is Worth More Than One 3D Gaussians in Single-View 3D Reconstruction<br>`A_Pixel_Is_Worth_More_Than_One_3D_Gaussians_in_Single_View_3D_Reconstruction` | neural-rendering-3d | gaussian_splatting.py, pixels_to_gaussians.py, unet.py | matplotlib, numpy, Pillow, torch, tqdm | CUDA, assets, writes |
| Adam: A Method For Stochastic Optimization<br>`Adam_a_Method_For_Stochastic_Optimization` | optimization-meta-rl | adam.py | keras, matplotlib, numpy, seaborn, torch, tqdm | CUDA, assets, writes |
| Adversarial Feature Learning<br>`Adversarial_Feature_Learning` | generative-models | adversarial_feature_learning.py | keras, matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Adversarially Learned Inference<br>`Adversarially_Learned_Inference` | generative-models | ali.py | matplotlib, scipy, torch, tqdm | CUDA, assets, writes |
| Auto-Encoding Variational Bayes<br>`Auto_Encoding_Variational_Bayes` | generative-models | VAEs.py | none listed | assets, writes |
| Conditional Generative Adversarial Nets<br>`Conditional_Generative_Adversarial_Nets` | generative-models | cgan.py | keras, matplotlib, numpy, torch, tqdm | assets, writes |
| DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling<br>`DPM_Solver_A_Fast_ODE_Solver_for_Diffusion_Probabilistic_Model_Sampling_in_Around_10_Steps` | generative-models | dpm_solver.py, unet.py | matplotlib, numpy, torch, tqdm | assets, writes |
| Deep Image Prior<br>`Deep_Image_Prior` | optimization-meta-rl | deep_image_prior.py | matplotlib, numpy, Pillow, torch, tqdm | assets, writes |
| Deep Reinforcement Learning with Double Q-learning<br>`Deep_Reinforcement_Learning_with_Double_Q_learning` | optimization-meta-rl | ddqn.py | gym, matplotlib, numpy, stable_baselines3, torch, tqdm | assets, writes |
| Deep Unsupervised Learning using Nonequilibrium Thermodynamics<br>`Deep_Unsupervised_Learning_using_Nonequilibrium_Thermodynamics` | generative-models | diffusion_models.py | matplotlib, numpy, sklearn, torch, tqdm | CUDA, assets, writes |
| Denoising Diffusion Implicit Models<br>`Denoising_Diffusion_Implicit_Models` | generative-models | ddim.py, unet.py | keras, matplotlib, numpy, torch, tqdm | assets, writes |
| Denoising Diffusion Probabilistic Models<br>`Denoising_Diffusion_Probabilistic_Models` | generative-models | diffusion_models.py, unet.py | keras, matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Density estimation using Real NVP<br>`Density_Estimation_Using_Real_NVP` | generative-models | real_nvp.py | matplotlib, numpy, torch, torchvision, tqdm | assets, download, writes |
| DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation<br>`DreamBooth_Fine_Tuning_Text_to_Image_Diffusion_Models_for_Subject_Driven_Generation` | generative-models | dreambooth.py | diffusers, matplotlib, Pillow, torch, torchvision, tqdm... | assets, download, writes |
| FastNeRF: High-Fidelity Neural Rendering at 200FPS<br>`FastNeRF_High_Fidelity_Neural_Rendering_at_200FPS` | neural-rendering-3d | fast_nerf.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Fast and Accurate Deep Network Learning by Exponential Linear Units (ELUs)<br>`Fast_and_Accurate_Deep_Network_Learning_by_Exponential_Linear_Units_ELUs` | optimization-meta-rl | elu.py | matplotlib, keras, numpy, seaborn, sklearn, torch... | CUDA, assets, writes |
| Flow Straight and Fast: Learning to Generate and Transfer Data with Rectified Flow<br>`Flow_Straight_and_Fast_Learning_to_Generate_and_Transfer_Data_with_Rectified_Flow` | generative-models | flow_straight_and_fast.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains<br>`Fourier_Features_Let_Networks_Learn_High_Frequency_Functions_in_Low_Dimensional_Domains` | neural-rendering-3d | inverse_rendering.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| FreeNeRF: Improving Few-shot Neural Rendering with Free Frequency Regularization<br>`FreeNeRF_Improving_Few_shot_Neural_Rendering_with_Free_Frequency_Regularization` | neural-rendering-3d | freenerf.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Gaussian Error Linear Units (GELUs)<br>`Gaussian_Error_Linear_Units_GELUs` | optimization-meta-rl | gelu.py | matplotlib, keras, numpy, seaborn, sklearn, torch... | CUDA, assets, writes |
| Generative Adversarial Networks<br>`Generative_Adversarial_Networks` | generative-models | GANs.py | Keras, matplotlib, numpy, torch, tqdm | assets, writes |
| Gromov-Wasserstein Distances between Gaussian Distributions<br>`Gromov_Wasserstein_Distances_between_Gaussian_Distributions` | generative-models | GWOT.py | matplotlib, torch | assets, writes |
| Stable Diffusion v1-5 / High-Resolution Image Synthesis with Latent Diffusion Models<br>`High_Resolution_Image_Synthesis_with_Latent_Diffusion_Models` | generative-models | model.py, sample.py | numpy, Pillow, safetensors, torch, tqdm, transformers | assets, download, writes |
| Human-level control through deep reinforcement learning<br>`Human_level_control_through_deep_reinforcement_learning` | optimization-meta-rl | dqn.py | gym, matplotlib, numpy, stable_baselines3, torch, tqdm | assets, writes |
| Image-to-Image Translation with Conditional Adversarial Networks<br>`Image_to_Image_Translation_with_Conditional_Adversarial_Nets` | generative-models | pix2pix.py | matplotlib, numpy, pillow, torch, torchvision, tqdm | CUDA, assets, writes |
| Implicit Neural Representations with Periodic Activation Functions<br>`Implicit_Neural_Representations_with_Periodic_Activation_Functions` | neural-rendering-3d | siren.py | matplotlib, numpy, skimage, torch, tqdm | CUDA, assets, writes |
| Improved Techniques for Training GANs<br>`Improved_Techniques_for_Training_GANs` | generative-models | semi_supervised_learning.py | keras, matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Improved Training of Wasserstein GANs<br>`Improved_Training_of_Wasserstein_GANs` | generative-models | wgan.py | matplotlib, numpy, pillow, torch, torchvision, tqdm | CUDA, assets, writes |
| InfoNeRF: Ray Entropy Minimization for Few-Shot Neural Volume Rendering<br>`InfoNeRF_Ray_Entropy_Minimization_for_Few_Shot_Neural_Volume_Rendering` | neural-rendering-3d | infonerf.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Instant Neural Graphics Primitives with a Multiresolution Hash Encoding<br>`Instant_Neural_Graphics_Primitives_with_a_Multiresolution_Hash_Encoding` | neural-rendering-3d | ngp.py | numpy, pillow, torch, tqdm | CUDA, assets, writes |
| K-Planes: Explicit Radiance Fields in Space, Time, and Appearance<br>`KPlanes_Explicit_Radiance_Fields_in_Space_Time_and_Appearance` | neural-rendering-3d | kplanes.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| KiloNeRF: Speeding up Neural Radiance Fields with Thousands of Tiny MLPs<br>`KiloNeRF_Speeding_up_Neural_Radiance_Fields_with_Thousands_of_Tiny_MLPs` | neural-rendering-3d | kilo_nerf.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Learned Initializations for Optimizing Coordinate-Based Neural Representations<br>`Learned_Initializations_for_Optimizing_Coordinate_Based_Neural_Representations` | optimization-meta-rl | nerf_mv.py | imageio, json, matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Least Squares Generative Adversarial Networks<br>`Least_Squares_Generative_Adversarial_Networks` | generative-models | lsgan.py | matplotlib, numpy, seaborn, torch, tqdm | CUDA, assets, writes |
| Light Field Networks: Neural Scene Representations with Single-Evaluation Rendering<br>`Light_Field_Networks_Neural_Scene_Representations_with_Single_Evaluation_Rendering` | neural-rendering-3d | lfn.py | matplotlib, numpy, Pillow, torch, tqdm | CUDA, assets, writes |
| Likelihood-free MCMC with Amortized Approximate Ratio Estimators<br>`Likelihood_free_MCMC_with_Amortized_Approximate_Ratio_Estimators` | generative-models | AALR-MCMC.py | matplotlib, torch, tqdm | assets, writes |
| Masked Autoregressive Flow for Density Estimation<br>`Masked_Autoregressive_Flow_for_Density_Estimation` | generative-models | maf.py | keras, matplotlib, numpy, torch, tqdm | assets, writes |
| Maxout Networks<br>`Maxout_Networks` | optimization-meta-rl | maxout_networks.py | keras, matplotlib, numpy, seaborn, torch, tqdm | CUDA, assets, writes |
| Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks<br>`Model_Agnostic_Meta_Learning_for_Fast_Adaptation_of_Deep_Networks` | optimization-meta-rl | maml.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Multiplicative Filter Networks<br>`Multiplicative_Filter_Networks` | neural-rendering-3d | mfn.py | matplotlib, numpy, skimage, torch, torchvision, tqdm | CUDA, assets, writes |
| NICE: Non-linear Independent Components Estimation<br>`NICE_Non_linear_Independent_Components_Estimation` | generative-models | NICE.py | Keras, matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis<br>`NeRF_Representing_Scenes_as_Neural_Radiance_Fields_for_View_Synthesis` | neural-rendering-3d | nerf.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Network In Network<br>`Network_In_Network` | optimization-meta-rl | nin.py | keras, matplotlib, numpy, seaborn, torch | CUDA, assets, writes |
| NeRF--: Neural Radiance Fields Without Known Camera Parameters<br>`Neural_Radiance_Fields_Without_Known_Camera_Parameters` | neural-rendering-3d | nerfmm.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| On First-Order Meta-Learning Algorithms<br>`On_First_Order_Meta_Learning_Algorithms` | optimization-meta-rl | reptile.py | matplotlib, numpy, torch, tqdm | assets, writes |
| On the Variance of the Adaptive Learning Rate and Beyond<br>`On_the_Variance_of_the_Adaptive_Learning_Rate_and_Beyond` | optimization-meta-rl | radam.py | keras, matplotlib, numpy, seaborn, torch, tqdm | CUDA, assets, writes |
| Optimizing Millions of Hyperparameters by Implicit Differentiation<br>`Optimizing_Millions_of_Hyperparameters_by_Implicit_Differentiation` | optimization-meta-rl | gradient_based_HO.py | Keras, matplotlib, numpy, torch, torchvision, tqdm... | assets, writes |
| Playing Atari with Deep Reinforcement Learning<br>`Playing_Atari_with_Deep_Reinforcement_Learning` | optimization-meta-rl | dqn.py | gym, matplotlib, numpy, stable_baselines3, torch, tqdm | assets, writes |
| PlenOctrees for Real-time Rendering of Neural Radiance Fields<br>`PlenOctrees_for_Real_time_Rendering_of_Neural_Radiance_Fields` | neural-rendering-3d | nerf-sg.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Plenoxels: Radiance Fields without Neural Networks<br>`Plenoxels_Radiance_Fields_without_Neural_Networks` | neural-rendering-3d | plenoxels.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Proximal Policy Optimization Algorithms<br>`Proximal_Policy_Optimization_Algorithms` | optimization-meta-rl | ppo.py | gym, matplotlib, numpy, stable_baselines3, torch, tqdm | CUDA, assets, writes |
| Pseudo Numerical Methods for Diffusion Models on Manifolds<br>`Pseudo_Numerical_Methods_for_Diffusion_Models_on_Manifolds` | generative-models | pndms_solver.py, unet.py | matplotlib, torch, tqdm | assets, writes |
| Self-Normalizing Neural Networks<br>`Self_Normalizing_Neural_Networks` | optimization-meta-rl | selu.py | keras, matplotlib, numpy, seaborn, scikit-learn, torch... | CUDA, assets, writes |
| Sequential Neural Likelihood: Fast Likelihood-free Inference with Autoregressive Flows<br>`Sequential_Neural_Likelihood` | generative-models | snl.py | matplotlib, torch, tqdm, UMNN | CUDA, assets, writes |
| Speedy-Splat: Fast 3D Gaussian Splatting with Sparse Pixels and Sparse Primitives<br>`Speedy_Splat_Fast_3D_Gaussian_Splatting_with_Sparse_Pixels_and_Sparse_Primitives` | neural-rendering-3d | speedy_splat.py | torch, numpy, pillow, tqdm | CUDA, assets, writes |
| Spherical Voronoi: Directional Appearance as a Differentiable Partition of the Sphere<br>`Spherical_Voronoi_Directional_Appearance_as_a_Differentiable_Partition_of_the_Sphere` | neural-rendering-3d | 3dgs_sv.py | torch, numpy, pillow, tqdm | CUDA, assets, writes |
| Splatter Image: Ultra-Fast Single-View 3D Reconstruction<br>`Splatter_Image_Ultra_Fast_Single_View_3D_Reconstruction` | neural-rendering-3d | gaussian_splatting.py, splatter_image.py, unet.py | matplotlib, numpy, Pillow, torch, tqdm | CUDA, assets, writes |
| CycleGAN<br>`Unpaired_Image_to_Image_Translation_using_Cycle_Consistent_Adversarial_Networks` | generative-models | cycle_gan.py | matplotlib, numpy, pillow, torch, torchvision, tqdm | CUDA, assets, writes |
| Unsupervised Representation Learning with Deep Convolutional Generative Adversarial Networks<br>`Unsupervised_Representation_Learning_with_Deep_Convolutional_Generative_Adversarial_Networks` | generative-models | conv_gan.py | matplotlib, numpy, torch, torchvision, tqdm | assets, writes |
| Variational Inference with Normalizing Flows<br>`Variational_Inference_with_Normalizing_Flows` | generative-models | Flows.py | matplotlib, numpy, torch, tqdm | CUDA, assets, writes |
| Wasserstein GAN<br>`Wasserstein_GAN` | generative-models | wgan.py | matplotlib, numpy, pillow, torch, torchvision, tqdm | CUDA, assets, writes |

## Dependency planning patterns

- **Torch dominates:** most entries pin Torch, often with old or CUDA-specific variants. Match the selected entry's Torch/Torchvision pair; do not reuse a modern environment blindly.
- **Keras/MNIST examples:** optimizer/layer/GAN entries often combine Keras dataset loaders with Torch models. Keras versions range from old 2.x to 3.x; imports can initiate dataset-cache behavior.
- **Rendering entries:** NeRF/3DGS/Splatter-style entries often require camera data, trained Gaussians, or dataset archives, plus hard-coded CUDA and image/GIF output directories.
- **Stable Diffusion/DreamBooth:** expect model weights, tokenizers, Diffusers/Transformers/Safetensors, high memory pressure, and network/download risk if weights are not already local.
- **RL entries:** DQN/DDQN/PPO depend on Gym and Stable-Baselines versions and may require Atari/ALE/ROM setup plus long training budgets.
- **Suspicious pins:** treat `json==2.0.9`, `sklearn==...`, `skimage==...`, and mixed package-name casing as catalog facts to review before installing; they may require translation or omission in a modern environment.

## Worked lookup patterns

### Stable Diffusion

- Match query terms: `stable diffusion`, `latent diffusion`, `high resolution image synthesis`, `sample.py`, `safetensors`, `transformers`.
- Catalog route: `generative-models`.
- Safety plan: warn about external weights/tokenizer access, download risk, output images, memory/GPU expectations, and no training support in the compact entry.

### Adam

- Match query terms: `adam`, `stochastic optimization`, `adam.py`, optimizer.
- Catalog route: `optimization-meta-rl`.
- Safety plan: use the optimizer/layer route for adaptation; do not run the full example by default because requirements are old, the evidence includes CUDA, output writes, and likely dataset behavior.

### NeRF

- Match query terms: `nerf`, `radiance field`, `view synthesis`, `nerf.py`, `novel views`.
- Catalog route: `neural-rendering-3d`.
- Safety plan: warn about external dataset/camera assets, CUDA, long optimization/rendering, and output folders; produce a tiny adaptation or static review plan instead of full training.
