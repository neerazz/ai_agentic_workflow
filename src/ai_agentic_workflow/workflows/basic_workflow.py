from langchain.chains.llm import LLMChain
from langchain.chains.sequential import SequentialChain

from langchain_core.prompts import PromptTemplate

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient

# 1. Instantiate clients
chat_client = DualModelChatClient()
claude_client = DualModelClaudeClient()
perplexity_client = DualModelPerplexityClient()
gemini_client = DualModelGeminiClient()

# 2. Load prompt templates from files
with open("prompts/breakdown_prompt.txt") as f:
    txt = f.read()
    breakdown_prompt = PromptTemplate(
        template=txt,
        input_variables=["question"],
    )

with open("prompts/summary_prompt.txt") as f:
    txt = f.read()
    summary_prompt = PromptTemplate(
        template=txt,
        input_variables=["question"],
    )

breakdown_prompt = PromptTemplate(input_variables=["question"], template=breakdown_prompt)
summary_prompt = PromptTemplate(input_variables=["question"], template=summary_prompt)

# 3. Define chains
# Use default reasoning model for breakdown
breakdown_chain = LLMChain(
    llm=chat_client.get_llm(),  # defaults to reasoning
    prompt=breakdown_prompt,
    output_key="breakdown"
)

# Use concept model for summary
summary_chain = LLMChain(
    llm=chat_client.get_llm(model_type="concept"),
    prompt=summary_prompt,
    output_key="summary"
)

# 4. Compose workflow
workflow_chain = SequentialChain(
    chains=[breakdown_chain, summary_chain],
    input_variables=["question"],
    output_variables=["breakdown", "summary"],
    verbose=True
)


# 5. Basic entrypoint
def run_basic(question: str) -> dict:
    """Runs the basic workflow and returns breakdown and summary."""
    return workflow_chain.run({"question": question})


if __name__ == '__main__':
    response = run_basic("Explain me what is an AI Agent")
    print(f"Final Response :\n {response}")
