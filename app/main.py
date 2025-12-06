# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import openai
from openai import OpenAI
import logging
import time
from typing import AsyncGenerator

from app.config import settings
from app.models import (
    InferenceRequest, 
    InferenceResponse, 
    HealthResponse
)

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready LLM inference service with rate limiting and observability"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Metrics tracking (simple counters for now)
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_tokens": 0
}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns service status and configuration
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        model=settings.OPENAI_MODEL
    )


@app.post("/v1/inference", response_model=InferenceResponse)
@limiter.limit(settings.RATE_LIMIT)
async def generate_inference(inference_request: InferenceRequest, request: Request):
    """
    Generate LLM inference
    
    This endpoint accepts a list of chat messages and returns a completion.
    Rate limited to prevent abuse.
    
    If stream=true in the request, use /v1/inference/stream endpoint instead.
    """
    start_time = time.time()
    metrics["total_requests"] += 1
    
    # If streaming is requested, redirect to streaming endpoint
    if inference_request.stream:
        raise HTTPException(
            status_code=400, 
            detail="For streaming responses, use POST /v1/inference/stream"
        )
    
    try:
        logger.info(f"Processing inference request with {len(inference_request.messages)} messages")
        
        # Call OpenAI API (non-streaming)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[msg.model_dump() for msg in inference_request.messages],
            max_tokens=inference_request.max_tokens,
            temperature=inference_request.temperature,
            stream=False
        )
        
        # Extract response data
        completion = response.choices[0]
        content = completion.message.content
        
        # Update metrics
        metrics["successful_requests"] += 1
        metrics["total_tokens"] += response.usage.total_tokens
        
        # Log performance
        duration = time.time() - start_time
        logger.info(f"Request completed in {duration:.2f}s, tokens: {response.usage.total_tokens}")
        
        return InferenceResponse(
            id=response.id,
            model=response.model,
            content=content,
            finish_reason=completion.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
        
    except openai.RateLimitError as e:
        metrics["failed_requests"] += 1
        logger.error(f"OpenAI rate limit exceeded: {e}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded at OpenAI")
    
    except openai.APIError as e:
        metrics["failed_requests"] += 1
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    
    except Exception as e:
        metrics["failed_requests"] += 1
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def stream_openai_response(inference_request: InferenceRequest) -> AsyncGenerator[str, None]:
    """
    Stream tokens from OpenAI API
    
    This is an async generator that yields chunks of text as they arrive.
    """
    try:
        logger.info(f"Starting streaming request with {len(inference_request.messages)} messages")
        
        # Call OpenAI API with streaming enabled
        stream = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[msg.model_dump() for msg in inference_request.messages],
            max_tokens=inference_request.max_tokens,
            temperature=inference_request.temperature,
            stream=True  # Enable streaming
        )
        
        # Iterate over the stream
        for chunk in stream:
            # Extract the content delta (the new text)
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    # Yield the token as Server-Sent Events format
                    yield f"data: {delta.content}\n\n"
        
        # Send end-of-stream marker
        yield "data: [DONE]\n\n"
        
        metrics["successful_requests"] += 1
        logger.info("Streaming request completed successfully")
        
    except openai.RateLimitError as e:
        metrics["failed_requests"] += 1
        logger.error(f"OpenAI rate limit exceeded during streaming: {e}")
        yield f"data: [ERROR] Rate limit exceeded\n\n"
    
    except openai.APIError as e:
        metrics["failed_requests"] += 1
        logger.error(f"OpenAI API error during streaming: {e}")
        yield f"data: [ERROR] LLM service error: {str(e)}\n\n"
    
    except Exception as e:
        metrics["failed_requests"] += 1
        logger.error(f"Unexpected error during streaming: {e}")
        yield f"data: [ERROR] Internal server error\n\n"


@app.post("/v1/inference/stream")
@limiter.limit(settings.RATE_LIMIT)
async def generate_inference_stream(inference_request: InferenceRequest, request: Request):
    """
    Generate LLM inference with streaming
    
    This endpoint streams tokens as they're generated, similar to ChatGPT.
    Returns Server-Sent Events (SSE) format.
    """
    metrics["total_requests"] += 1
    
    return StreamingResponse(
        stream_openai_response(inference_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/metrics")
async def get_metrics():
    """
    Prometheus-style metrics endpoint
    Returns basic usage statistics
    """
    return {
        "total_requests": metrics["total_requests"],
        "successful_requests": metrics["successful_requests"],
        "failed_requests": metrics["failed_requests"],
        "total_tokens_processed": metrics["total_tokens"],
        "success_rate": (
            metrics["successful_requests"] / metrics["total_requests"] 
            if metrics["total_requests"] > 0 else 0
        )
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "health": "/health",
            "inference": "/v1/inference",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)