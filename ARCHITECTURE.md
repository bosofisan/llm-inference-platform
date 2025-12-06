# Architecture Overview

## High-Level Architecture
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────────────────────────┐
│     Kubernetes Service          │
│   (Load Balancer / ClusterIP)   │
└────────────┬────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐     ┌─────────┐
│ Pod 1   │     │ Pod 2   │  ◄── HPA scales 2-10 pods
│ FastAPI │     │ FastAPI │
└────┬────┘     └────┬────┘
     │               │
     └───────┬───────┘
             ▼
      ┌─────────────┐
      │  OpenAI API │
      └─────────────┘
```

## Component Breakdown

### Application Layer
- **FastAPI Server**: Async Python web framework
  - Handles HTTP requests
  - Streams LLM responses
  - Rate limiting middleware
  - Health checks

### Kubernetes Resources
- **Deployment**: Manages 2 replica pods (scales 2-10)
- **Service**: ClusterIP exposing port 80 → pod port 8000
- **HPA**: Auto-scales based on CPU (70%) and memory (80%)
- **ConfigMap**: Stores non-sensitive configuration
- **Secret**: Stores OpenAI API key (base64 encoded)

### Request Flow

1. **Client** sends POST to `/v1/inference`
2. **Service** load balances to available pod
3. **Rate Limiter** checks request count (10/min limit)
4. **FastAPI** validates request with Pydantic
5. **OpenAI Client** calls GPT API
6. **Response** returned (streaming or complete)
7. **Metrics** updated

## Resource Management
```
Per Pod:
├── CPU Request: 250m (0.25 cores)
├── CPU Limit: 500m (0.5 cores)
├── Memory Request: 256Mi
└── Memory Limit: 512Mi

Cluster Total (2 pods):
├── CPU: 500m-1000m
└── Memory: 512Mi-1024Mi
```

## Scaling Behavior
```
Load Low (CPU < 70%)
├── Pods: 2 (minimum)
└── State: Stable

Load Moderate (CPU 70-85%)
├── Pods: 3-5
└── Action: Scale up gradually

Load High (CPU > 85%)
├── Pods: 6-10 (maximum)
└── Action: Scale up quickly

Load Decreases
├── Wait: 5 minutes (stabilization window)
└── Scale down: 50% per minute (gradual)
```

## Failure Handling

### Pod Failures
- Liveness probe fails → Kubernetes restarts pod
- Readiness probe fails → Remove from service endpoints
- Container crash → Automatic restart with backoff

### API Failures
- Rate limit hit → HTTP 429 response
- Timeout → HTTP 504 after 30s
- Invalid request → HTTP 422 with details

## Security Layers

1. **Container**: Non-root user (UID 1000)
2. **Secrets**: Base64 encoded, mounted as env vars
3. **Network**: ClusterIP (internal only by default)
4. **Resource Limits**: Prevents resource exhaustion
