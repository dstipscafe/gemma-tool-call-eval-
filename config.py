API_BASE_URL = "http://192.168.0.254:8000/v1"
API_KEY = "not-needed"  # llama.cpp doesn't require a real key
MODEL_NAME = "gemma-4-27b"  # model name served by llama.cpp

# Evaluation settings
MAX_RETRIES = 3
REQUEST_TIMEOUT = 120  # seconds
CONCURRENCY = 1  # sequential by default to avoid overloading
RESULTS_DIR = "results"
