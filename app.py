from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cachetools import LRUCache
import requests
import time
import psutil
import logging
from typing import Dict, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Llama 3 8B API",
    description="REST API wrapper for Llama 3 8B model with caching and performance tracking",
    version="1.0.0"
)

# Initialize LRU cache with a maximum size of 1000 items
cache = LRUCache(maxsize=1000)

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7

class PerformanceMetrics:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.cpu_percent = 0
        self.memory_percent = 0

    def start(self):
        self.start_time = time.time()
        self.cpu_percent = psutil.cpu_percent()
        self.memory_percent = psutil.virtual_memory().percent

    def end(self, input_text: str, output_text: str):
        self.end_time = time.time()
        self.input_tokens = len(input_text.split())
        self.output_tokens = len(output_text.split())
        
        metrics = {
            "inference_latency_ms": round((self.end_time - self.start_time) * 1000, 2),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cpu_usage_percent": self.cpu_percent,
            "memory_usage_percent": self.memory_percent
        }
        
        logger.info(f"Performance metrics: {json.dumps(metrics)}")
        return metrics

def get_ollama_response(prompt: str, max_tokens: int, temperature: float) -> Dict:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Ollama API: {str(e)}")
        raise HTTPException(status_code=500, detail="Error communicating with Ollama service")

@app.post("/generate")
async def generate_text(request: GenerateRequest):
    # Create cache key from request parameters
    cache_key = f"{request.prompt}:{request.max_tokens}:{request.temperature}"
    
    # Check cache
    if cache_key in cache:
        logger.info("Cache hit")
        return cache[cache_key]
    
    # Initialize performance tracking
    metrics = PerformanceMetrics()
    metrics.start()
    
    try:
        # Get response from Ollama
        response = get_ollama_response(
            request.prompt,
            request.max_tokens,
            request.temperature
        )
        
        # Calculate performance metrics
        perf_metrics = metrics.end(request.prompt, response.get("response", ""))
        
        # Prepare final response
        result = {
            "response": response.get("response", ""),
            "metrics": perf_metrics
        }
        
        # Store in cache
        cache[cache_key] = result
        logger.info("Cache miss - stored new response")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "cache_size": len(cache)} 