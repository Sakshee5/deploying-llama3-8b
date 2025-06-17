# Llama 3 8B API Wrapper

A FastAPI-based REST API wrapper for the Llama 3 8B model, featuring LRU caching and comprehensive performance tracking.

## Features

- REST API endpoint for text generation using Llama 3 8B
- LRU (Least Recently Used) caching for improved performance
- Detailed performance metrics tracking
- Health check endpoint
- Comprehensive logging

## Prerequisites

- Python 3.8+
- Ollama installed and running locally with Llama 3 8B model
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Ensure Ollama is running with the Llama 3 8B model:
```bash
ollama run llama2
```

## Usage

1. Start the FastAPI server:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

2. The API will be available at `http://localhost:8000`

3. Access the interactive API documentation at `http://localhost:8000/docs`

### API Endpoints

#### POST /generate
Generate text using the Llama 3 8B model.

Request body:
```json
{
    "prompt": "Your prompt here",
    "max_tokens": 100,  // optional, default: 100
    "temperature": 0.7  // optional, default: 0.7
}
```

Response:
```json
{
    "response": "Generated text...",
    "metrics": {
        "inference_latency_ms": 123.45,
        "input_tokens": 10,
        "output_tokens": 50,
        "cpu_usage_percent": 45.2,
        "memory_usage_percent": 60.1
    }
}
```

#### GET /health
Check the API health status.

Response:
```json
{
    "status": "healthy",
    "cache_size": 42
}
```

## Performance Tracking

The API automatically tracks and logs the following metrics:
- Inference latency (in milliseconds)
- Input and output token counts
- CPU usage percentage
- Memory usage percentage

Logs are written to both `api.log` and stdout.

## Caching

The API implements an LRU cache with a maximum size of 1000 items. Cache keys are generated based on the prompt, max_tokens, and temperature parameters.

## Error Handling

The API includes comprehensive error handling for:
- Ollama service unavailability
- Invalid requests
- Internal server errors

All errors are logged with appropriate context.
