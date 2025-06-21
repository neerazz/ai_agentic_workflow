# Project: AI Agent Workflow

## 📁 Project Structure

This project is organized to facilitate the development and execution of AI-driven workflows using multiple AI models. Below is an overview of the directory structure and its responsibilities.

```plaintext
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
│   ├── advanced_workflow.py       # Complex orchestration with decision logic
│   └── youtube_wisdom_workflow.py # Advanced workflow with quality gates
│   └── youtube_video_workflow.py  # CrewAI-based YouTube generation workflow
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

- **[clients/](src/ai_agentic_workflow/clients/)**: Contains one module per AI provider, each defining dual-model facades and `__call__` methods.
- **[workflows/](src/ai_agentic_workflow/workflows/)**: Defines chains that orchestrate multiple clients. Split into simple vs. advanced pipelines.
- **[prompts/](src/ai_agentic_workflow/prompts/)**: Stores prompt templates in text files for easy editing and reuse.
- **[utils/](src/ai_agentic_workflow/utils/)**: Shared utilities (e.g., scoring, validation, retry decorators).
- **[automation/](src/ai_agentic_workflow/automation/)**: Scripts that drive browsers via Selenium.
- **[tools/](src/ai_agentic_workflow/tools/)**: Helpers for third-party services like Notion.
- **[examples/](examples/)**: CLI scripts or small demos showing how to run workflows end-to-end.
- **[notebooks/](src/ai_agentic_workflow/notebooks/)**: Interactive demos and prototyping notebooks.
- **[tests/](tests/)**: Unit and integration tests for robustness.
- **README.md**: High-level project description, setup, and contribution guidelines.
- **YouTube workflow**: Generates 4-5 minute inspirational videos for adults using multiple AI models.
- **Wisdom workflow**: Advanced pipeline with critique loops for higher-quality inspirational videos.

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/ai-agent-workflow.git
   cd ai-agent-workflow
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy the `.env.example` file to `.env`
   - Fill in your API keys and other required variables in the `.env` file:

     ```ini
     OPENAI_API_KEY=your_openai_api_key
     ANTHROPIC_API_KEY=your_anthropic_api_key
     PERPLEXITY_API_KEY=your_perplexity_api_key
     GOOGLE_API_KEY=your_google_api_key
     ```

### Running Tests

To ensure everything is set up correctly, run the test suite:

```bash
python -m pytest tests/
```

### Running Examples

Check out the example scripts in the `workflows/` directory to get started:

```bash
python workflows/blog_creation_workflow.py
```

For more detailed examples and usage, refer to the Jupyter notebook in `notebooks/agent_workflow.ipynb`.
