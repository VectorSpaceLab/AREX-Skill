# Colossal-LLaMA, ColossalEval, ColossalQA, and ColossalMoE

## Colossal-LLaMA

Use for continual pretraining and supervised fine-tuning of LLaMA-family models. Typical stages: prepare tokenizer/model, prepare datasets, choose command-line arguments, launch training, and run checkpoint inference when assets are available.

## ColossalEval

Use for LLM evaluation pipelines. The flow is dataset conversion, inference config, evaluation config, and metric/judge summarization. ColossalEval has its own package and dependencies, including evaluation/data science packages and optional vLLM/OpenAI paths.

## ColossalQA

Use for document retrieval conversation systems. The design includes document loading, text splitting, vector store construction, retrieval, prompt formatting, local/API LLM inference, and conversation memory.

Important cautions: it can pin older PyTorch and LangChain versions compared with core ColossalAI; API-style LLMs require credentials and endpoints; local LLMs require model checkpoints and GPU memory; vector stores require persistent directories and schema decisions.

## ColossalMoE

Use for Mixture-of-Experts training and inference examples. Expect CUDA GPUs, Transformers, datasets, and model assets. Route topology and MoE hybrid plugin details back to the core parallelism and Booster sub-skills.
