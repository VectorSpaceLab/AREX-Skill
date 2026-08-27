# Optimization, Bedrock, and recommendations

Use this file for post-build optimization, deployment recommendations, and
Bedrock deployment paths.

## Optimization

`ModelBuilder.optimize(...)` is the path for serving-time optimization. It is
used when the goal is to change the runtime characteristics of the model before
or during deployment.

Use it when the user asks about:

- quantization
- compilation
- sharding
- speculative decoding
- right-sizing a deployment

## Deployment recommendations

`ModelBuilder.generate_deployment_recommendations(...)` runs the inference
recommender workflow and returns a recommendation job.
The job can then be inspected or turned back into a builder flow.

Related artifacts:

- `BenchmarkJob`
- `RecommendationJob`
- `start_benchmark(...)`

## Bedrock deployment

`BedrockModelBuilder` handles the Bedrock path.
It supports:

- Nova custom-model creation and deployment
- model import jobs for other model families
- `deploy(...)` with resource reuse support

## When to choose which path

| Need | Use |
| --- | --- |
| optimize a SageMaker endpoint or local serving config | `optimize()` |
| compare deployment options before creating the endpoint | `generate_deployment_recommendations()` |
| deploy to Bedrock instead of SageMaker | `BedrockModelBuilder.deploy()` |

## Operational notes

- Reuse can avoid duplicate endpoint creation and duplicate recommendation jobs.
- Recommendation and optimization flows still need region and AWS credentials.
- Bedrock deployments should be treated as billable cloud operations.
