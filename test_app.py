import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app, cache, PerformanceMetrics
import json

client = TestClient(app)

@pytest.fixture
def mock_ollama_response():
    return {
        "response": "This is a test response",
        "done": True
    }

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "cache_size": len(cache)}

@pytest.mark.asyncio
async def test_generate_text_cache_hit():
    # Prepare test data
    test_prompt = "Test prompt"
    test_data = {
        "prompt": test_prompt,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    # Create cache entry
    cache_key = f"{test_prompt}:100:0.7"
    cache[cache_key] = {
        "response": "Cached response",
        "metrics": {
            "inference_latency_ms": 0,
            "input_tokens": 2,
            "output_tokens": 2,
            "cpu_usage_percent": 0,
            "memory_usage_percent": 0
        }
    }
    
    response = client.post("/generate", json=test_data)
    assert response.status_code == 200
    assert response.json()["response"] == "Cached response"

@pytest.mark.asyncio
async def test_generate_text_cache_miss(mock_ollama_response):
    with patch('app.requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_ollama_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        test_data = {
            "prompt": "New test prompt",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = client.post("/generate", json=test_data)
        assert response.status_code == 200
        assert "response" in response.json()
        assert "metrics" in response.json()

def test_performance_metrics():
    metrics = PerformanceMetrics()
    metrics.start()
    
    # Simulate some processing time
    import time
    time.sleep(0.1)
    
    result = metrics.end("test input", "test output")
    assert "inference_latency_ms" in result
    assert "input_tokens" in result
    assert "output_tokens" in result
    assert "cpu_usage_percent" in result
    assert "memory_usage_percent" in result
    assert result["input_tokens"] == 2
    assert result["output_tokens"] == 2

@pytest.mark.asyncio
async def test_error_handling():
    with patch('app.requests.post') as mock_post:
        mock_post.side_effect = Exception("Test error")
        
        test_data = {
            "prompt": "Error test",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = client.post("/generate", json=test_data)
        assert response.status_code == 500
        assert "detail" in response.json() 