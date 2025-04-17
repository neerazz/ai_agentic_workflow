# Project: AI Agent Workflow

## 📁 Project Structure
```
ai-agent-workflow/
├── .env                          # Environment variables for API keys
├── clients/
│   ├── __init__.py                # Package for AI client wrappers
│   ├── chat_client.py             # DualModelChatClient implementation
│   ├── claude_client.py           # DualModelClaudeClient implementation
│   ├── perplexity_client.py       # DualModelPerplexityClient implementation
│   └── gemini_client.py           # GeminiClient stub
│
├── workflows/
│   ├── __init__.py                # Package for workflow definitions
│   ├── basic_workflow.py          # Simple SequentialChain example
│   └── advanced_workflow.py       # Complex orchestration with decision logic
│
├── prompts/
│   ├── breakdown_prompt.txt       # Prompt template for breakdown tasks
│   └── summary_prompt.txt         # Prompt template for summaries
│
├── utils/
│   ├── __init__.py                # Utility functions package
│   ├── env_reader.py              # Reads .env variables
│   └── scoring.py                 # Hallucination scoring and validation logic
│
├── examples/
│   ├── run_basic.py               # Example script invoking basic_workflow
│   └── run_advanced.py            # Example script showing full pipeline with retries
│
├── notebooks/
│   └── agent_workflow.ipynb       # Jupyter notebook demo (original code)
│
├── tests/
│   ├── test_clients.py            # Unit tests for client wrappers
│   └── test_workflows.py          # Tests for workflow logic and retry behavior
│
├── requirements.txt               # Python dependencies
├── README.md                      # Project overview and setup instructions
└── .gitignore                     # Exclude env, __pycache__, etc.
```

### Directory Responsibilities
- **clients/**: Contains one module per AI provider, each defining dual-model facades and `__call__` methods.
- **workflows/**: Defines chains that orchestrate multiple clients. Split into simple vs. advanced pipelines.
- **prompts/**: Stores prompt templates in text files for easy editing and reuse.
- **utils/**: Shared utilities (e.g., scoring, validation, retry decorators).
- **examples/**: CLI scripts or small demos showing how to run workflows end-to-end.
- **notebooks/**: Interactive demos and prototyping notebooks.
- **tests/**: Unit and integration tests for robustness.
- **README.md**: High-level project description, setup, and contribution guidelines.
