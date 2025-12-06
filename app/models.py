# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, List

class ChatMessage(BaseModel):
    """A single message in a chat conversation"""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")

class InferenceRequest(BaseModel):
    """Request body for inference endpoint"""
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: Optional[int] = Field(500, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(False, description="Enable streaming response")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {"role": "user", "content": "What is machine learning?"}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "stream": False
                }
            ]
        }
    }

class InferenceResponse(BaseModel):
    """Response body for inference endpoint"""
    id: str = Field(..., description="Unique response ID")
    model: str = Field(..., description="Model used for generation")
    content: str = Field(..., description="Generated text")
    finish_reason: str = Field(..., description="Why generation stopped")
    usage: dict = Field(..., description="Token usage statistics")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    model: str = Field(..., description="LLM model in use")