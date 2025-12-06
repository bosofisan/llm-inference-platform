#!/bin/bash

echo "🚀 LLM Inference Platform - Quick Start"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install Docker."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found. Please install kubectl."; exit 1; }
echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OPENAI_API_KEY"
    exit 1
fi

# Build Docker image
echo -e "${BLUE}Building Docker image...${NC}"
docker build -t llm-inference-platform:v1.0 .
echo -e "${GREEN}✓ Image built${NC}"
echo ""

# Check cluster
echo -e "${BLUE}Checking Kubernetes cluster...${NC}"
kubectl cluster-info > /dev/null 2>&1 || { echo "❌ No Kubernetes cluster found"; exit 1; }
echo -e "${GREEN}✓ Cluster connected${NC}"
echo ""

# Create namespace
echo -e "${BLUE}Creating namespace...${NC}"
kubectl create namespace llm-demo 2>/dev/null || echo "Namespace already exists"
kubectl config set-context --current --namespace=llm-demo
echo ""

# Deploy
echo -e "${BLUE}Deploying to Kubernetes...${NC}"
kubectl apply -f k8s/
echo -e "${GREEN}✓ Deployed${NC}"
echo ""

# Wait for pods
echo -e "${BLUE}Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=llm-api --timeout=120s
echo -e "${GREEN}✓ Pods ready${NC}"
echo ""

# Show status
echo "📊 Deployment Status:"
kubectl get all
echo ""

echo "🎉 Deployment complete!"
echo ""
echo "To access the API:"
echo "  kubectl port-forward service/llm-api-service 8080:80"
echo ""
echo "Then visit:"
echo "  http://localhost:8080/docs    (API documentation)"
echo "  http://localhost:8080/health  (Health check)"
echo "  http://localhost:8080/metrics (Metrics)"
