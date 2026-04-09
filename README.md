# Gemma Tool Call Eval

An evaluation framework for measuring LLM tool calling (function calling) capabilities. Built to benchmark [Gemma 4 27B](https://ai.google.dev/gemma) served via [llama.cpp](https://github.com/ggerganov/llama.cpp), but works with any OpenAI-compatible API.

## Overview

This framework sends 150 structured test cases to the model and evaluates how accurately it selects tools and fills in parameters. It covers:

- **10 tools** across 3 complexity levels (simple / medium / complex)
- **4 test types**: direct, inference, edge case, and distractor
- **6 core metrics**: JSON validity, tool selection, parameter completeness, parameter accuracy, format compliance, and optional parameter handling

## Project Structure

```
gemma-tool-call-eval/
├── config.py                 # API endpoint and model settings
├── main.py                   # CLI entry point
├── tools/
│   ├── definitions.py        # 10 tool schemas (OpenAI function calling format)
│   └── mock_handlers.py      # Mock responses for tool execution
├── test_cases/
│   └── cases.py              # 150 test cases with expected outputs
├── eval/
│   ├── runner.py              # Evaluation engine (sends requests, parses responses)
│   └── metrics.py             # Metrics computation and aggregation
└── results/                   # Generated reports (JSON + CSV)
```

## Tools

### Simple (1-2 params)
| Tool | Description |
|------|-------------|
| `get_current_weather` | Get weather for a city |
| `get_exchange_rate` | Currency exchange rate lookup |
| `get_time_in_timezone` | Current time in a timezone |

### Medium (3-5 params, optional params, enums)
| Tool | Description |
|------|-------------|
| `search_products` | Product search with category, price, and sort filters |
| `send_email` | Send email with optional CC and priority |
| `book_restaurant` | Restaurant reservation |
| `calculate_loan` | Loan payment calculator |

### Complex (nested objects, arrays)
| Tool | Description |
|------|-------------|
| `create_calendar_event` | Calendar event with recurrence rules |
| `search_flights` | Flight search with passenger breakdown |
| `create_order` | Order with item list, shipping address, and payment |

## Test Case Design

Each tool has 15 test cases (150 total):

| Type | Count | Description |
|------|-------|-------------|
| **Direct** | 50 | Prompt explicitly states all parameter values |
| **Inference** | 50 | Model must reason to determine parameter values |
| **Edge** | 30 | Boundary values, format variants, optional param handling |
| **Distractor** | 20 | Irrelevant information mixed in to test focus |

Prompts are a mix of English (~70%) and Chinese (~30%) to test multilingual ability.

## Metrics

| Metric | Description |
|--------|-------------|
| Valid JSON Rate | Whether the tool call response is parseable JSON |
| Tool Selection Accuracy | Whether the correct tool was chosen |
| Parameter Completeness | Whether all required parameters are present |
| Parameter Accuracy | Whether parameter values match expected values |
| Format Compliance | Whether parameter types match the schema |
| Optional Parameter Handling | Whether relevant optional params are filled when context clues are present |

Results are grouped by **complexity level**, **test type**, and **individual tool**.

## Quick Start

### Prerequisites

- Python 3.10+
- [llama.cpp](https://github.com/ggerganov/llama.cpp) built with GPU support
- A GGUF model file (e.g., `gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf`)

### Start the Model Server

```bash
~/.unsloth/llama.cpp/build/bin/llama-server \
    --model ~/playground/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
    --host 0.0.0.0 \
    --port 8000 \
    --n-gpu-layers 99 \
    --ctx-size 8192
```

This launches an OpenAI-compatible API at `http://<your-ip>:8000/v1`. Key flags:
- `--n-gpu-layers 99`: offload all layers to GPU for maximum speed
- `--ctx-size 8192`: context window size (adjust based on available VRAM)

**Test Environment:**
- GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)
- Driver: 580.126.09 / CUDA 13.0
- VRAM Usage: ~18.3GB / 24.6GB with the Q4_K_XL quantized model loaded

### Setup

```bash
uv venv && uv pip install openai pydantic pandas
source .venv/bin/activate
```

### Configuration

Edit `config.py` to point to your API:

```python
API_BASE_URL = "http://192.168.0.254:8000/v1"
MODEL_NAME = "gemma-4-27b"
```

### Run

```bash
# Quick smoke test (10 cases, 1 per tool)
python main.py --quick

# Full evaluation (150 cases)
python main.py

# Filter by dimension
python main.py --complexity simple
python main.py --type direct
python main.py --tool weather

# Run without saving results
python main.py --no-save
```

### Output

- Terminal: summary table with all metrics
- `results/report_<timestamp>.json`: full report with per-case details
- `results/summary_<timestamp>.csv`: spreadsheet-friendly summary

## Sample Results (Gemma 4 27B)

| Metric | Score |
|--------|-------|
| Valid JSON Rate | 98.7% |
| Tool Selection Accuracy | 98.7% |
| Parameter Completeness | 98.7% |
| Parameter Accuracy | 74.7% |
| Format Compliance | 98.7% |
| Optional Param Handling | 95.3% |
| Avg Response Time | 758ms |

**By Complexity:**

| Level | Param Accuracy | Avg Latency |
|-------|---------------|-------------|
| Simple | 84.4% | 616ms |
| Medium | 75.0% | 651ms |
| Complex | 64.4% | 1042ms |

**By Test Type:**

| Type | Param Accuracy |
|------|---------------|
| Distractor | 90% |
| Direct | 84% |
| Edge | 80% |
| Inference | 56% |

## License

MIT
