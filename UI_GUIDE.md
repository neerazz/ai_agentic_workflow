# 🎨 General Purpose Agent - UI Guide

Two beautiful interfaces for interacting with the General Purpose Agent: a **web-based UI (Gradio)** and an **enhanced CLI** with live progress tracking.

---

## 🌐 Web UI (Gradio)

**Beautiful browser-based chat interface with real-time progress visualization**

### Features

✅ **Chat Interface**
- Clean, modern chat bubbles
- Full conversation history displayed
- Multi-turn conversations with context memory
- Markdown rendering for formatted responses

✅ **Real-Time Progress**
- Live progress bar updates
- Current stage indicator with emojis
- Task completion tracking (X/Y tasks done)
- Quality score display (0.00-1.00)
- Retry attempt counter

✅ **Configuration Panel**
- Easy provider selection (Free/Default/Accurate/Local)
- One-click agent initialization
- Cost estimates displayed
- Configuration validation feedback

✅ **Conversation Management**
- Clear chat button
- View full conversation history
- Automatic context from previous turns
- Session persistence

### Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 General Purpose Agent                                    │
│ Self-improving AI with critique loops                       │
├──────────────────────────────────┬──────────────────────────┤
│ 💬 Conversation                  │ ⚙️ Configuration         │
│                                  │ ○ Free Tier ($0/month)   │
│ You: What is Python?             │ ○ Default ($10-20/month) │
│                                  │ ○ Accurate ($20-30/mo)   │
│ AI: Python is a high-level...    │ ○ Local (LM Studio)      │
│     ⏱️ 3.2s | 📋 5 tasks          │                          │
│     ⭐ Quality: 0.87/1.00         │ [Initialize Agent 🚀]    │
│                                  │ ✅ Agent ready           │
│ ┌─────────────────────────────┐  │                          │
│ │ Your message...             │  │ 📊 Real-Time Progress    │
│ └─────────────────────────────┘  │ ✨ Synthesizing          │
│ [Send 📤]                        │ ████████████░░░░ 75%     │
│                                  │ Tasks: 4/5 completed     │
│ [Clear 🗑️] [History 📜]          │ Quality: 0.82/1.00       │
│                                  │ Attempt: 1/3             │
└──────────────────────────────────┴──────────────────────────┘
```

### Usage

**1. Install dependencies:**
```bash
pip install gradio
```

**2. Launch the web UI:**
```bash
python examples/general_purpose_agent_gradio.py
```

**3. Open browser:**
- Navigate to: `http://localhost:7860`
- The UI will open automatically in most systems

**4. Initialize agent:**
- Select configuration (Free Tier recommended)
- Click "Initialize Agent 🚀"
- Wait for "✅ Agent ready"

**5. Start chatting:**
- Type your question in the message box
- Watch real-time progress in the right panel
- Review conversation history anytime

### Configuration Options

| Configuration | Cost | Best For |
|--------------|------|----------|
| **Free Tier** | $0/month | Testing, personal use, zero budget |
| **Default** | $10-20/month | Production, balanced quality |
| **Accurate** | $20-30/month | High-stakes, maximum quality |
| **Local** | $0/month | Privacy, offline, LM Studio required |

### API Keys

Set environment variables for your chosen providers:

```bash
# For Free Tier
export GOOGLE_API_KEY="your-gemini-key"
export GROQ_API_KEY="your-groq-key"

# For Default
export ANTHROPIC_API_KEY="your-claude-key"
export OPENAI_API_KEY="your-openai-key"

# For Accurate
export ANTHROPIC_API_KEY="your-claude-key"
export OPENAI_API_KEY="your-openai-key"

# For Local (no keys needed, just run LM Studio)
```

---

## 💻 Enhanced CLI

**Terminal-based interface with live progress bars and rich formatting**

### Features

✅ **Live Progress Visualization**
- Real-time progress tables
- Animated progress bars
- Stage indicators with emojis
- Task breakdown display

✅ **Rich Formatting**
- Markdown rendering in terminal
- Color-coded output
- Bordered panels and tables
- Syntax highlighting

✅ **Interactive Commands**
- `/help` - Show available commands
- `/history` - View conversation history
- `/clear` - Clear conversation
- `/quit` - Exit application

✅ **Smart Progress Tracking**
- Shows current stage (Clarifying → Planning → Executing → etc.)
- Task completion counter
- Quality score for each task
- Retry attempt tracking

### Screenshots

```
════════════════════════════════════════════════════════════════
🤖 General Purpose Agent - Enhanced CLI
════════════════════════════════════════════════════════════════

⚙️  Configuration: Free Tier (Gemini + Groq) - $0/month
✅ Agent initialized successfully!

You: What are the benefits of Python?

╭────────────────── 🤖 Agent Progress ──────────────────╮
│ Stage       │ ⚙️ Executing                            │
│ Progress    │ ████████████████░░░░░░░░░░░░░░ 60%     │
│ Tasks       │ 3/5 completed                           │
│ Current     │ Compare Python to other languages       │
│ Quality     │ 0.78/1.00                               │
╰─────────────────────────────────────────────────────────╯

╭────────────────── 📋 Task Breakdown ───────────────────╮
│ #  │ Task                            │ Status    │ Score │
├────┼─────────────────────────────────┼───────────┼───────┤
│ 1  │ List Python benefits            │ ✅ Done   │ 0.82  │
│ 2  │ Explain each benefit            │ ✅ Done   │ 0.79  │
│ 3  │ Compare to other languages      │ 🔄 Working│ -     │
│ 4  │ Provide code examples           │ ⏳ Pending│ -     │
│ 5  │ Summarize key takeaways         │ ⏳ Pending│ -     │
╰─────────────────────────────────────────────────────────╯

╭────────────────── ✅ Agent Response ────────────────────╮
│                                                          │
│ # Benefits of Python                                     │
│                                                          │
│ Python offers several key advantages:                    │
│                                                          │
│ 1. **Readability** - Clean, English-like syntax         │
│ 2. **Versatility** - Web, data science, AI, automation  │
│ 3. **Large Ecosystem** - 300,000+ packages              │
│ 4. **Community** - Extensive support and resources      │
│ ...                                                      │
│                                                          │
╰──────────────────────────────────────────────────────────╯

⏱️ 4.2s | 📋 5 tasks | ⭐ Quality: 0.85/1.00
```

### Usage

**1. Launch the enhanced CLI:**
```bash
python examples/general_purpose_agent_cli_enhanced.py
```

**2. Select configuration:**
```
Select configuration [1-4, default=1]: 1
```

**3. Wait for initialization:**
```
✅ Agent initialized successfully!
```

**4. Start asking questions:**
```
You: What is machine learning?
```

**5. Watch live progress:**
- Progress table updates in real-time
- Task breakdown shows each step
- Quality scores displayed per task

### Commands

| Command | Description |
|---------|-------------|
| `<your question>` | Ask the agent anything |
| `/help` | Show available commands and tips |
| `/history` | View full conversation history |
| `/clear` | Clear conversation (start fresh session) |
| `/quit` or `/exit` | Exit the application |

### Progress Stages

The agent goes through these stages:

1. **❓ Clarifying** - Assessing confidence, asking follow-ups if needed
2. **📋 Planning** - Breaking down request into tasks (with critique)
3. **⚙️ Executing** - Running each task (with critique per task)
4. **🔍 Critiquing** - Evaluating task quality, suggesting improvements
5. **✨ Synthesizing** - Combining results (with critique)
6. **✅ Completed** - Final response ready

### Quality Scores

- **0.00-0.59** 🔴 Low quality - Agent will retry (attempt 2-3)
- **0.60-0.74** 🟡 Acceptable - May retry if not improving
- **0.75-1.00** 🟢 High quality - Accepted immediately

---

## 🆚 Comparison: Web UI vs Enhanced CLI

| Feature | Gradio Web UI | Enhanced CLI |
|---------|--------------|--------------|
| **Access** | Browser (any device) | Terminal only |
| **Setup** | One command | One command |
| **Progress** | Auto-refreshing panel | Live table updates |
| **History** | Scroll up or click button | `/history` command |
| **Best For** | Teams, sharing, demos | Developers, server access |
| **Network** | Can expose publicly | Local only |
| **Speed** | Slower (network overhead) | Faster (direct) |
| **Mobile** | ✅ Yes (responsive) | ❌ No |
| **Keyboard** | Standard typing | Terminal shortcuts |
| **Copy/Paste** | Easy | Terminal-dependent |

---

## 🚀 Quick Start Examples

### Example 1: Research Question

**Input:**
```
What are the latest developments in quantum computing?
```

**Progress You'll See:**
1. ❓ Clarifying (confidence: 85% - no follow-up needed)
2. 📋 Planning (5 tasks planned, critique accepted on attempt 1)
3. ⚙️ Executing
   - Task 1: Recent breakthroughs ✅ (score: 0.82)
   - Task 2: Key companies ✅ (score: 0.79)
   - Task 3: Technical advances ✅ (score: 0.88)
   - Task 4: Future implications ✅ (score: 0.81)
   - Task 5: Summary ✅ (score: 0.85)
4. ✨ Synthesizing (final output, score: 0.87, accepted)
5. ✅ Completed

### Example 2: Multi-Turn Conversation

**Turn 1:**
```
You: Explain neural networks
AI: [Detailed explanation with 0.84 quality score]
```

**Turn 2:**
```
You: How does the first concept you mentioned compare to traditional ML?
AI: [Uses context from Turn 1, explains backpropagation vs. traditional approaches]
```

**Turn 3:**
```
You: Give me a code example from our previous discussion
AI: [Provides neural network code, references previous explanation]
```

### Example 3: Low Quality Retry

**Progress:**
1. 📋 Planning - Attempt 1 (score: 0.62 - RETRY)
2. 📋 Planning - Attempt 2 (score: 0.79 - ACCEPT ✅)
3. ⚙️ Executing Task 1 - Attempt 1 (score: 0.58 - RETRY)
4. ⚙️ Executing Task 1 - Attempt 2 (score: 0.77 - ACCEPT ✅)
5. ✨ Synthesizing - Attempt 1 (score: 0.71 - RETRY)
6. ✨ Synthesizing - Attempt 2 (score: 0.83 - ACCEPT ✅)

---

## 🐛 Troubleshooting

### Gradio UI Issues

**Port already in use:**
```bash
# Change port in the code (line ~360):
demo.launch(server_port=7861)  # Use different port
```

**Can't access from other devices:**
```bash
# Enable sharing (in the code):
demo.launch(share=True)  # Creates public link
```

**Progress updates:**
- Progress updates when you send a message or the agent responds
- Updates are immediate and reflect the current state
- No background auto-refresh (better compatibility across Gradio versions)

### Enhanced CLI Issues

**Progress table not updating:**
- Check terminal supports ANSI colors
- Try standard CLI: `python examples/general_purpose_agent_cli.py`

**Unicode characters broken:**
```bash
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
```

**Slow rendering:**
- Normal for complex responses
- Use simpler queries for faster results

### General Issues

**API Key errors:**
```bash
# Check keys are set
echo $GOOGLE_API_KEY
echo $GROQ_API_KEY

# Set missing keys
export GOOGLE_API_KEY="your-key-here"
```

**Import errors:**
```bash
pip install -r requirements.txt
```

**Agent initialization fails:**
- Check API keys
- Verify internet connection
- Try Free Tier configuration first
- Check logs for specific errors

---

## 📊 Performance Tips

### For Best Speed

1. **Use Free Tier** - Groq is extremely fast
2. **Keep questions focused** - Fewer tasks = faster execution
3. **Avoid multiple retries** - High confidence questions perform better
4. **Use Enhanced CLI** - No network overhead

### For Best Quality

1. **Use Accurate config** - Best models
2. **Allow retries** - Quality threshold set to 0.75
3. **Provide context** - Clearer questions get better results
4. **Review critique scores** - Learn what works well

### For Zero Cost

1. **Use Free Tier** - $0/month
2. **Or use Local** - LM Studio required
3. **Gemini**: 1,500 requests/day free
4. **Groq**: 14,400 requests/day free

---

## 🎯 Next Steps

**Try it out:**
```bash
# Web UI
python examples/general_purpose_agent_gradio.py

# Enhanced CLI
python examples/general_purpose_agent_cli_enhanced.py

# Basic CLI (simpler, no live progress)
python examples/general_purpose_agent_cli.py
```

**Customize:**
- Modify progress refresh rate
- Change UI colors/themes
- Adjust quality thresholds
- Add custom commands

**Extend:**
- Add more progress visualizations
- Integrate with external tools
- Create custom agents using BaseAgent
- Build domain-specific interfaces

---

## 📚 Additional Resources

- **General Purpose Agent README**: See `GENERAL_PURPOSE_AGENT_README.md`
- **Main README**: See `README.md`
- **Configuration Guide**: See `src/ai_agentic_workflow/config/defaults.py`
- **Agent Documentation**: See `src/ai_agentic_workflow/agents/`

---

**Enjoy your self-improving AI agent! 🚀**
