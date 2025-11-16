# Agentic Workflow Orchestrator

A sophisticated, model-agnostic orchestrator for AI-powered workflow automation with multi-stage reasoning, confidence scoring, and greedy task execution.

## 🌟 Features

- **Model-Agnostic Design**: Support for multiple AI providers (OpenAI, Anthropic, Google, Groq, DeepSeek, LM Studio, Perplexity)
- **Confidence Scoring**: Multi-dimensional analysis to ensure sufficient understanding before execution
- **Intelligent Clarification**: Automatic user clarification when confidence is below threshold
- **AI-Powered Task Planning**: Breaks down complex requests into executable tasks with dependencies
- **Greedy Execution**: Optimal task execution strategy for best possible results
- **Comprehensive Logging**: Structured logging with full tracing for debuggability
- **Extensible Architecture**: Easy to add new providers, executors, or strategies
- **Fail-Fast Support**: Quick error detection with configurable retry logic

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Query                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 1: Confidence Assessment                          │
│  • Clarity scoring                                       │
│  • Completeness analysis                                 │
│  • Feasibility evaluation                                │
│  • Specificity measurement                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────┴──────────┐
          │ Confidence >= 70%?   │
          └──────────┬──────────┘
                Yes  │  No
                     │  └─────────────────┐
                     ▼                    ▼
         ┌──────────────────┐  ┌──────────────────────┐
         │  Skip to Stage 3 │  │ Stage 2: Clarification│
         └─────────┬────────┘  │  • Formulate questions │
                   │            │  • Get user responses  │
                   │            │  • Enhance query       │
                   │            └──────────┬─────────────┘
                   │                       │
                   └───────────┬───────────┘
                               ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 3: Task Planning                                  │
│  • Break down into tasks                                 │
│  • Identify dependencies                                 │
│  • Define success criteria                               │
│  • Determine data sources                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 4: Task Execution (Greedy Strategy)               │
│  • Select highest priority ready task                    │
│  • Execute optimally                                     │
│  • Validate against success criteria                     │
│  • Retry on failure                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 5: Output Synthesis                               │
│  • Aggregate task results                                │
│  • Generate coherent response                            │
│  • Return to user                                        │
└─────────────────────────────────────────────────────────┘
```

## 📦 Components

### Core Modules

- **`orchestrator/`**: Main orchestration logic
  - `core_orchestrator.py`: Entry point and workflow coordinator
  - `confidence_scorer.py`: Multi-dimensional confidence analysis
  - `clarification_handler.py`: User interaction and clarification
  - `task_planner.py`: AI-powered task breakdown
  - `task_executor.py`: Greedy task execution

- **`llm/`**: Model-agnostic AI interface
  - `model_manager.py`: Unified provider management
  - `providers/`: Provider implementations
    - `base_provider.py`: Abstract base class
    - `openai_provider.py`: OpenAI integration
    - `anthropic_provider.py`: Anthropic Claude integration
    - `lmstudio_provider.py`: Local model support

- **`config/`**: Configuration management
  - `orchestrator_config.py`: Configuration classes
  - `defaults.py`: Pre-configured settings

- **`logging/`**: Logging and tracing
  - `structured_logger.py`: Rich contextual logging
  - `trace_manager.py`: End-to-end request tracing

## 🚀 Quick Start

### Installation

```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

### Basic Usage

```python
from ai_agentic_workflow.orchestrator import Orchestrator
from ai_agentic_workflow.config import get_default_config

# Create orchestrator
orchestrator = Orchestrator(get_default_config())

# Process a query
result = orchestrator.process("Explain how neural networks work")

# Print results
result.print_summary()
```

### Using Local Models (LM Studio)

```python
from ai_agentic_workflow.orchestrator import Orchestrator
from ai_agentic_workflow.config import get_local_lmstudio_config

# Configure for local LM Studio
config = get_local_lmstudio_config()
config.model.lmstudio_base_url = "http://localhost:1234/v1"

orchestrator = Orchestrator(config)
result = orchestrator.process("Your query here")
```

### Custom Configuration

```python
from ai_agentic_workflow.config import (
    OrchestratorConfig,
    ModelConfig,
    ConfidenceConfig,
    ModelProvider,
)

config = OrchestratorConfig(
    model=ModelConfig(
        orchestrator_provider=ModelProvider.ANTHROPIC,
        orchestrator_model="claude-3-5-sonnet-20241022",
        planner_provider=ModelProvider.OPENAI,
        planner_model="gpt-4o",
    ),
    confidence=ConfidenceConfig(
        min_confidence_threshold=0.80,
        max_clarification_rounds=3,
    ),
)

orchestrator = Orchestrator(config)
```

## 🎯 Configuration Options

### Model Configuration

```python
ModelConfig(
    # Orchestrator model (reasoning and confidence scoring)
    orchestrator_provider=ModelProvider.ANTHROPIC,
    orchestrator_model="claude-3-5-sonnet-20241022",
    orchestrator_temperature=0.7,

    # Planner model (task breakdown)
    planner_provider=ModelProvider.OPENAI,
    planner_model="gpt-4o",
    planner_temperature=0.3,

    # Executor model (task execution)
    executor_provider=ModelProvider.ANTHROPIC,
    executor_model="claude-3-5-sonnet-20241022",
    executor_temperature=0.5,
)
```

### Confidence Configuration

```python
ConfidenceConfig(
    min_confidence_threshold=0.75,  # 0.0 - 1.0
    max_clarification_rounds=3,
    auto_clarify=True,

    # Confidence dimension weights (must sum to 1.0)
    clarity_weight=0.30,
    completeness_weight=0.30,
    feasibility_weight=0.25,
    specificity_weight=0.15,
)
```

### Execution Configuration

```python
ExecutionConfig(
    strategy=ExecutionStrategy.GREEDY,  # GREEDY, SEQUENTIAL, PARALLEL
    max_retries=3,
    retry_backoff=1.0,  # seconds
    validate_results=True,
    fail_fast=True,
)
```

### Logging Configuration

```python
LoggingConfig(
    log_level="INFO",
    structured_logging=False,
    enable_tracing=True,
    log_model_calls=True,
    export_traces=True,
    trace_export_path="./traces",
)
```

## 🎨 Pre-configured Profiles

```python
from ai_agentic_workflow.config import get_config_by_name

# Available profiles:
config = get_config_by_name("default")      # Balanced production config
config = get_config_by_name("development")  # Debug mode with verbose logging
config = get_config_by_name("local")        # LM Studio local models
config = get_config_by_name("fast")         # Optimized for speed
config = get_config_by_name("accurate")     # Optimized for accuracy
```

## 📝 Examples

See the `examples/` directory for complete working examples:

- `basic_orchestrator_example.py`: Simple usage with default config
- `lmstudio_orchestrator_example.py`: Using local models via LM Studio
- `advanced_orchestrator_example.py`: Custom config with detailed analysis

Run an example:

```bash
python examples/basic_orchestrator_example.py
```

## 🔍 Understanding Results

```python
result = orchestrator.process("your query")

# Check success
if result.success:
    print("Success!")
else:
    print(f"Failed: {result.error}")

# Access components
print(f"Confidence: {result.confidence_score.overall}")
print(f"Tasks planned: {len(result.task_plan.tasks)}")
print(f"Execution time: {result.execution_time_seconds}s")

# Get final output
print(result.final_output)

# Save to JSON
with open("result.json", "w") as f:
    f.write(result.to_json())
```

## 🔧 Extending the Orchestrator

### Adding a New Provider

1. Create a new provider class inheriting from `BaseProvider`
2. Implement required methods: `generate()`, `generate_with_history()`, `get_provider_name()`
3. Add provider instantiation in `ModelManager._get_provider()`

```python
from ai_agentic_workflow.llm.providers.base_provider import BaseProvider

class MyCustomProvider(BaseProvider):
    def generate(self, prompt, system_prompt=None, **kwargs):
        # Implementation
        pass

    def generate_with_history(self, messages, **kwargs):
        # Implementation
        pass

    def get_provider_name(self):
        return "my_custom_provider"
```

### Adding Custom Task Sources

Extend `TaskExecutor._execute_by_source()` to support new task source types:

```python
# In your extended TaskExecutor class
def _execute_custom_source(self, task: Task) -> Any:
    # Custom execution logic
    pass
```

## 🐛 Debugging and Tracing

### Enable Detailed Logging

```python
from ai_agentic_workflow.logging import setup_logging

setup_logging(level="DEBUG", structured=True)
```

### Export Execution Trace

```python
from ai_agentic_workflow.logging import get_trace_manager

trace_manager = get_trace_manager()
trace_json = trace_manager.export_trace(result.trace_id)

with open("trace.json", "w") as f:
    f.write(trace_json)
```

### Common Issues

1. **API Key Missing**: Ensure environment variables are set:
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   ```

2. **Low Confidence**: The system will automatically ask clarification questions if enabled

3. **Task Execution Failures**: Check logs for detailed error messages and retry information

## 🧪 Testing

```bash
# Run basic test
python examples/basic_orchestrator_example.py

# Test with local models (requires LM Studio running)
python examples/lmstudio_orchestrator_example.py

# Run advanced test with full features
python examples/advanced_orchestrator_example.py
```

## 📊 Performance Considerations

- **Model Selection**: Faster models (GPT-4o-mini, Groq) for quick results vs. accuracy models (Claude Opus, GPT-4)
- **Confidence Threshold**: Lower threshold (0.70) for speed, higher (0.85) for accuracy
- **Validation**: Disable result validation for faster execution
- **Parallel Execution**: Coming soon for independent tasks

## 🤝 Contributing

To extend the orchestrator:

1. Maintain modularity - each component should be independently testable
2. Add comprehensive logging for debuggability
3. Follow the existing provider pattern for new integrations
4. Update configuration classes for new settings
5. Add examples demonstrating new features

## 📄 License

[Include your license information]

## 🙏 Acknowledgments

Built with:
- LangChain for AI orchestration patterns
- OpenAI, Anthropic, and other AI providers
- Python's rich ecosystem of tools
