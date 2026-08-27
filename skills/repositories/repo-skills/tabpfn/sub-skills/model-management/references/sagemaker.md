# SageMaker Endpoint Reference

This repository includes a SageMaker runtime example that targets an existing
TabPFN endpoint.

## What it is for

- Serializing tabular train/test arrays into a request payload.
- Invoking an already-deployed endpoint.
- Demonstrating how a hosted TabPFN 2.5 service could be called.

## What it is not for

- It is not a local inference workflow.
- It is not a replacement for the sklearn estimators.
- It is not a default runtime helper because it depends on an endpoint and AWS credentials.

## When to use this reference

Only when the user explicitly asks about the endpoint template or wants to adapt
it for their own SageMaker deployment.
