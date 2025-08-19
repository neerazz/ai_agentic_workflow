# Workflows Directory

End-to-end pipelines orchestrating multiple clients.

- [basic_workflow.py](basic_workflow.py) - Simple chain using several LLMs in sequence.
- [blackstone_workflow.py](blackstone_workflow.py) - Specialized workflow for investment-analysis style prompts.
- [youtube_video_workflow.py](youtube_video_workflow.py) - CrewAI example for creating short motivational videos.
- [youtube_wisdom_workflow.py](youtube_wisdom_workflow.py) - Advanced video workflow with critique and improvement loops.
- [stock_earnings_crewai_workflow.py](stock_earnings_crewai_workflow.py) - CrewAI workflow for earnings-based stock screening using Perplexity (browser) + ChatGPT.
- [basic_workflow.md](basic_workflow.md) - Example output from running the basic workflow.
- [__init__.py](__init__.py) - Package initializer.

## Stock Earnings CrewAI Workflow

CrewAI pipeline orchestrating:
- ChatGPT to fetch upcoming earnings list
- Perplexity in a persistent browser session (fallback to API) for analyses
- ChatGPT to select top 2 bullish candidates
- Predictions from both ChatGPT and Perplexity

Run:
```
python -m src.ai_agentic_workflow.workflows.stock_earnings_crewai_workflow
```

Environment variables required:
- `OPENAI_API_KEY`
- `PERPLEXITY_API_KEY`
