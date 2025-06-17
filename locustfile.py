from locust import HttpUser, task, between
import json

class LlamaAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_text(self):
        payload = {
            "prompt": "What is the capital of France?",
            "max_tokens": 100,
            "temperature": 0.7
        }
        self.client.post("/generate", json=payload)
    
    @task
    def health_check(self):
        self.client.get("/health") 