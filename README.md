# LLM Inference Platform

### Production-grad LLM serving with FastAPI, Kubernetes, Autoscaling, Streaming Responses, and Observability

This project is a full end-to-end LLM inference platform that demonstrates real-world ML infrastructure patterns: streaming token responses, rate limiting, autoscaling, fault tolerance, observability, and secure containerized deployments. It runs on AWS EKS, local clusters, or any Kubernetes environment. 

## Key Features
- #### FastAPI LLM inference API
    - Standard responses + Server-Sent Events (SSE) for real-time streaming
    - Fully async implementation for high concurrency 
- #### Production Kubernetes Deployment
    - Horizontal Pod Autoscaling (2 -> 10 replicas) based on CPU & memory
    - Zero-downtime rolling updates with ```maxSurge=1``` & ```maxUnavailable=0```
    - Liveness & readiness probes for 99.9% availability
    - Pod anti-affinity to spread replicas across nodes
    - Resource requests/limits to prevent noisy-neighbor scenarios
- #### Platform Reliability
    - IP-based rate limiting (10 req/min)
    - Graceful handling of OpenAI rate limit errors
    - Structured, contextual logging 
    - Full Prometheus metrics integration
- #### Secure, Optimized Containerization
    - Multi-stage Docker builds (200MB smaller image)
    - Non-root execution, minimal base image, locked-down filesystem
    - Secrets stored via Kubernetes Secrets, never in code
- #### Deployable Anywhere
    - AWS EKS
    - Local kind/minikube clusters
    - Any CNCF-compatible Kubernetes 

## Architecture Overview
                        ┌────────────────────────┐
                        │      Client / UI       │
                        └──────────┬─────────────┘
                                   │
                         HTTPS (REST / SSE)
                                   │
                       ┌───────────▼────────────┐
                       │       FastAPI API      │
                       │ - /inference           │
                       │ - /stream (SSE)        │
                       │ - /health /metrics     │
                       └───────────┬────────────┘
                                   │
                                   │ Async calls
                                   ▼
                    ┌────────────────────────────┐
                    │    OpenAI / LLM Provider   │
                    └────────────────────────────┘

        ┌──────────────────────────────────────────────────────────┐
        │                         Kubernetes                        │
        │  - Deployments        - ConfigMaps       - Secrets        │
        │  - Horizontal Pod Autoscaler (CPU & Mem)                  │
        │  - Rolling Updates    - Resource Limits  - Affinity Rules │
        └──────────────────────────────────────────────────────────┘

## Project Structure 
```
.
├── app/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── utils/
│   └── config.py
├── Dockerfile
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── configmap.yaml
│   └── secret.yaml
└── requirements.txt
```

## Getting Started (Local)
1. ### Install dependencies 
    ``` pip install -r requirements.txt ```
2. ### Set environment variable 
    ``` export OPENAI_API_KEY=your_key_here ```
3. ### Run locally
    ``` uvicorn app.main:app --reload ```
4. ### Test endpoints
    #### Standard inference:
    ```` curl -X POST http://localhost:8000/inference ````
    #### Streaming inference:
    ```` curl http://localhost:8000/stream ````

## Running with Docker
````bash
docker build -t llm-inference .
docker run -p 8000:8000 llm-inference 
````

## Deploying to Kubernetes
#### Apply manifests:
````bash 
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
````
#### Check rollout:
```` kubectl rollout status deployment/llm-service ````
#### View autoscaling:
```` kubectl get hpa llm-service ````

## Observability
#### Metrics
Prometheus-compatible endpoint:

```` /metrics ````

Tracks: 
- Request count
- Latencies 
- 429 rate-limit events
- Streaming vs non-streaming usage

#### Logging 
- Structured JSON logs
- Request ID correlation
- Error categorization 

## Security 

- Runs as non-root ``` UID 1000 ```
- Minimal ``` python:3.12-slim ``` base image
- Secrets via Kubernetes Secrets
- Resource limits preventing DoS
- Ready for TLS termination + NetworkPolicies 

## Image Optimization
Multi-stage Docker build reduces size by 200MG: 
- Stage 1: build deps
- Stage 2 copy compiled packages only
- Layer caching based on ``` requirements.txt ```

## Scaling Strategy
Horizontal Pod Autoscaler: 
- Min: 2 replicas
- Max: 10 replicas
- CPU target 70%
- Memory target: 80%
- Fast scale-up, conservative scale-down 
- Anti-affinity to spread across nodes

## Roadmap
- Add Redis-based request queue 
- Multi-provider support (OpenAI, Anthropic, Mistral)
- Response caching
- Authentication + per-user limits
- Integrate vLLM/TGI for self-hosted models
- Grafana dashboards with latency percentiles

## Why This Project Exists 
 
This platform was built to demonstrate LLM serving infrastructure, scalable backend engineering, and Kubernetes production operations; the same patterns used by teams at Scale AI, OpenAI, Anthropic, and other ML infra-heavy companies. 

It showcases:
- Real streaming
- Fault tolerance 
- Autoscaling
- Observability
- Secure containerization
- Infrastructure-as-code discipline 


