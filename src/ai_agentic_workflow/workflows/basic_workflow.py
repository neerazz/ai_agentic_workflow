import logging
from pathlib import Path

from langchain.chains.llm import LLMChain
from langchain.chains.sequential import SequentialChain
from langchain_core.prompts import PromptTemplate

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient

logger = logging.getLogger(__name__)

# 1. Instantiate clients
chat_client = DualModelChatClient()
claude_client = DualModelClaudeClient()
perplexity_client = DualModelPerplexityClient()
gemini_client = DualModelGeminiClient()

# 2. Load prompt templates from files
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PACKAGE_ROOT / "prompts"
# 2) Read in your prompt files by constructing absolute paths
breakdown_path = PROMPTS_DIR / "breakdown_prompt.txt"
summary_path = PROMPTS_DIR / "summary_prompt.txt"
# 2) Read the raw text into its own variable
breakdown_path = PROMPTS_DIR / "breakdown_prompt.txt"
summary_path = PROMPTS_DIR / "summary_prompt.txt"

with open(breakdown_path, "r", encoding="utf-8") as f:
    breakdown_template = f.read()

with open(summary_path, "r", encoding="utf-8") as f:
    summary_template = f.read()

breakdown_prompt = PromptTemplate(input_variables=["question"], template=breakdown_template)
summary_prompt = PromptTemplate(
    input_variables=["breakdown", "question"],
    template=summary_template
)

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
    logger.info(f"Starting basic workflow for question: {question!r}")
    outputs = workflow_chain.invoke({"question": question})

    # --- FIX ---
    # Log both outputs if desired
    logger.info(f"Breakdown: {outputs['breakdown'][:100]}...")
    logger.info(f"Summary: {outputs['summary'][:100]}...")

    # Return the whole dictionary containing both 'breakdown' and 'summary'
    return outputs


if __name__ == '__main__':
    # 1. Define the initial question
    input_question = "Explain me what is an AI Agent"

    # 2. Run the workflow and get the results dictionary
    response_data = run_basic(input_question)

    # 3. Format and print the output in sections
    box_width = 80  # Adjust width as needed
    separator = "-" * box_width

    print("\n" + "=" * box_width)
    print(" W O R K F L O W   O U T P U T")
    print("=" * box_width)

    # Section: Original Question
    print("\n[ Input Question ]")
    print(separator)
    print(input_question)  # Use the original input variable

    # Section: Breakdown
    # Use .get() with a default value in case the key is missing for some reason
    breakdown_output = response_data.get('breakdown', '--- Breakdown not generated ---')
    print("\n[ Generated Breakdown (Reasoning Model) ]")
    print(separator)
    print(breakdown_output)

    # Section: Summary
    summary_output = response_data.get('summary', '--- Summary not generated ---')
    print("\n[ Generated Summary (Concept Model) ]")
    print(separator)
    print(summary_output)

    print("\n" + "=" * box_width)  # Footer line
    print(" E N D   O F   O U T P U T")
    print("=" * box_width + "\n")
