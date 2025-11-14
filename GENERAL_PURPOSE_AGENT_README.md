# 🤖 General Purpose Agent - Self-Improving AI with Critique Loops

A sophisticated, critique-driven AI agent that **improves its own outputs** through iterative refinement. Uses free tier APIs for **$0/month operation** while maintaining high quality.

## 🌟 Key Features

### ✅ **Self-Improving Critique Loops**
- **Harsh, unbiased evaluation** of every output (no favoritism)
- **Up to 3 retry attempts** per task with improvement suggestions
- **Intelligent decision making** based on quality trends
- **Automatic stop** if not improving

### ✅ **Deep Task Reasoning**
- Breaks complex requests into **2-15 optimal tasks**
- Multi-stage reasoning: understanding → strategy → breakdown → optimization
- Identifies dependencies and execution approaches
- Enforces task count boundaries

### ✅ **Multi-Dimensional Quality Scoring**
- **Accuracy** (35% weight): Factually correct?
- **Completeness** (35% weight): Addresses all requirements?
- **Clarity** (15% weight): Well-structured?
- **Relevance** (15% weight): On-topic?

### ✅ **Progress Tracking**
- Real-time task status updates
- UI-ready structured data
- Workflow stages: clarifying → planning → executing → critiquing → synthesizing
- Progress callbacks for integration

### ✅ **Free Tier Operation**
- **Gemini 1.5 Pro**: 1,500 free requests/day
- **Groq Llama 3.1 70B**: 14,400 free requests/day
- **Monthly cost: $0** (vs $80 for subscriptions)

### ✅ **Extensible Architecture**
- BaseAgent template for custom agents
- Modular components (mix and match)
- Easy to create specialized agents

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API keys (free!)
export GOOGLE_API_KEY="your-gemini-api-key"
export GROQ_API_KEY="your-groq-api-key"
```

**Get free API keys:**
- Gemini: https://makersuite.google.com/app/apikey
- Groq: https://console.groq.com/keys

### Run CLI

```bash
python examples/general_purpose_agent_cli.py
```

### Python Usage

```python
from ai_agentic_workflow.agents import GeneralPurposeAgent
from ai_agentic_workflow.config import get_free_tier_config

# Initialize with free tier config ($0/month)
config = get_free_tier_config()
agent = GeneralPurposeAgent(config)

# Execute a request
result = agent.execute("Explain quantum computing and provide example use cases")

if result.success:
    print(result.output)
    print(f"Quality score: {result.metadata['final_critique']['quality_score']:.2f}")
```

---

## 📊 How It Works

### Complete Workflow

```
┌──────────────────────────────────────────────────────────┐
│  1. User Request                                         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  2. Confidence Assessment                                │
│     • Clarity, completeness, feasibility, specificity    │
│     • Threshold: 70-80%                                  │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼ (if confidence < threshold)
┌──────────────────────────────────────────────────────────┐
│  3. Clarification (Optional)                             │
│     • Formulate targeted questions                       │
│     • Get user responses                                 │
│     • Enhance query                                      │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  4. Deep Task Reasoning                                  │
│     • Understand core goal                               │
│     • Determine strategy                                 │
│     • Break into 2-15 tasks                              │
│     • Validate dependencies                              │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  5. Task Execution with Critique Loops                   │
│                                                           │
│     For each task (max 3 attempts):                      │
│                                                           │
│     ┌──────────────────┐                                 │
│     │  Execute Task    │                                 │
│     └────────┬─────────┘                                 │
│              │                                            │
│              ▼                                            │
│     ┌──────────────────┐                                 │
│     │ Harsh Critique   │                                 │
│     │ • Accuracy       │                                 │
│     │ • Completeness   │                                 │
│     │ • Clarity        │                                 │
│     │ • Relevance      │                                 │
│     └────────┬─────────┘                                 │
│              │                                            │
│              ▼                                            │
│     ┌──────────────────┐                                 │
│     │ Decision Maker   │                                 │
│     │ Accept/Retry?    │                                 │
│     └────────┬─────────┘                                 │
│              │                                            │
│         Retry│Accept                                     │
│      ────────┴────────                                   │
│      ↑               ↓                                    │
│ Apply improvements  Continue                             │
│                                                           │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  6. Output Synthesis                                     │
│     • Combine task results                               │
│     • Generate coherent response                         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  7. Final Critique                                       │
│     • Validate against original request                  │
│     • Overall quality assessment                         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
           Final Output
```

### Critique Loop Detail

Each task goes through up to 3 refinement cycles:

```python
Attempt 1:
  Execute → Critique (score: 0.65) → RETRY (improve clarity)

Attempt 2:
  Execute (with improvements) → Critique (score: 0.78) → ACCEPT ✓

Result: High-quality output
```

**Decision Logic:**
- ✅ **ACCEPT** if quality_score >= 0.75 and no critical issues
- 🔄 **RETRY** if improvable and attempts < 3
- ⚠️ **PROCEED** if max attempts reached (with warning)
- 🛑 **REJECT** if fundamentally flawed

---

## 🎯 Configuration Options

### 1. Free Tier (Recommended)

```python
from ai_agentic_workflow.config import get_free_tier_config

config = get_free_tier_config()
# Gemini + Groq = $0/month
```

### 2. Default (Balanced)

```python
from ai_agentic_workflow.config import get_default_config

config = get_default_config()
# Claude + GPT = ~$10-20/month
```

### 3. Accurate (Best Quality)

```python
from ai_agentic_workflow.config import get_config_by_name

config = get_config_by_name("accurate")
# Claude Opus + GPT-4 = ~$20-30/month
```

### 4. Local (LM Studio)

```python
config = get_config_by_name("local")
# Local models = $0/month (requires LM Studio)
```

---

## 🔧 Advanced Usage

### Custom Agent

```python
from ai_agentic_workflow.agents import BaseAgent, AgentResult

class MyCustomAgent(BaseAgent):
    """Custom agent for specific use case."""

    def execute(self, user_input, context=None):
        # Custom workflow
        # Can reuse components: critique_engine, task_reasoner, etc.

        return AgentResult(
            success=True,
            output="Custom output",
            metadata={"custom_key": "value"}
        )

# Use it
agent = MyCustomAgent(config)
result = agent.execute("My custom request")
```

### Progress Tracking for UI

```python
def my_progress_callback(progress_data):
    """Handle progress updates."""
    stage = progress_data['stage']
    percent = progress_data['progress_percent']
    tasks = progress_data['tasks']

    # Update UI
    print(f"Stage: {stage} ({percent}%)")

    for task in tasks['details']:
        print(f"  Task {task['task_id']}: {task['status']}")

agent = GeneralPurposeAgent(
    config=config,
    progress_callback=my_progress_callback
)
```

### Structured Logging

```python
from ai_agentic_workflow.logging import setup_logging

# Enable JSON structured logging
setup_logging(level="INFO", structured=True)

# Logs will include trace IDs, metadata, etc.
```

---

## 📈 Cost Comparison

| Option | Monthly Cost | Quality | Speed |
|--------|--------------|---------|-------|
| **Free Tier (Gemini+Groq)** | **$0** | ⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ |
| Paid Subscriptions | $80 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| API (optimized) | $10-20 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ |
| Local (LM Studio) | $0 | ⭐⭐⭐ | ⚡⚡ |

**Savings with free tier: $960/year!**

---

## 🎨 Components Overview

### CritiqueEngine
- Harsh, unbiased evaluation
- Multi-dimensional scoring
- Critical issue identification
- Improvement suggestions

### DecisionMaker
- Intelligent retry logic
- Quality trend analysis
- Max retry enforcement
- Improvement detection

### TaskReasoner
- Deep request understanding
- 2-15 task breakdown
- Dependency analysis
- Strategy optimization

### ProgressTracker
- Real-time status updates
- UI-ready data structures
- Workflow stage tracking
- Time and progress metrics

### BaseAgent
- Extensible template
- Common lifecycle
- Error handling
- Standard interface

### GeneralPurposeAgent
- Complete workflow implementation
- Integrates all components
- Progress callbacks
- Full logging/tracing

---

## 🐛 Debugging

### Enable Debug Logging

```python
from ai_agentic_workflow.logging import setup_logging

setup_logging(level="DEBUG", structured=True)
```

### Export Trace

```python
from ai_agentic_workflow.logging import get_trace_manager

result = agent.execute("...")

# Export trace
trace_manager = get_trace_manager()
trace_json = trace_manager.export_trace(result.metadata['trace_id'])

with open("trace.json", "w") as f:
    f.write(trace_json)
```

### View Progress

```python
result = agent.execute("...")

# Get detailed progress
progress = result.metadata['progress']

for task in progress['tasks']['details']:
    print(f"{task['task_id']}: {task['status']} ({task['progress_percent']}%)")
    if task['critique_score']:
        print(f"  Quality: {task['critique_score']:.2f}")
```

---

## 📚 Examples

See `examples/` directory for:
- `general_purpose_agent_cli.py`: Interactive CLI
- `basic_orchestrator_example.py`: Simple API usage
- `advanced_orchestrator_example.py`: Advanced features

---

## 🤝 Contributing

To create a custom specialized agent:

1. Inherit from `BaseAgent`
2. Implement `execute()` method
3. Reuse components as needed (critique, task_reasoner, etc.)
4. Return `AgentResult`

Example use cases for custom agents:
- Code generation with testing
- Research with source citation
- Content creation with SEO optimization
- Data analysis with visualization
- Documentation generation

---

## 📄 License

[Include your license]

---

## 🙏 Acknowledgments

Built with:
- **Gemini** (Google AI)
- **Groq** (Ultra-fast inference)
- **Anthropic** (Claude)
- **OpenAI** (GPT models)
- Rich ecosystem of open-source tools

---

**🎉 Ready to use! Start with $0/month cost using free tier.**

```bash
python examples/general_purpose_agent_cli.py
```
