import logging
import re
from pathlib import Path

from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate

# Assuming your clients are accessible, adjust imports if needed
from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient

# from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
# from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
# from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient

logger = logging.getLogger(__name__)

# --- Configuration ---
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PACKAGE_ROOT / "prompts"

# Use one client for simplicity, or swap as needed
# Choose the client you want to use primarily
llm_client = DualModelChatClient(
    reasoning_model="gpt-4o-mini",  # Or your preferred reasoning model
    concept_model="gpt-3.5-turbo"  # Or your preferred concept model
)


# llm_client = DualModelClaudeClient()
# llm_client = DualModelGeminiClient()
# llm_client = DualModelPerplexityClient()


# --- Load Prompts ---
def load_prompt(filename: str) -> str:
    """Loads a prompt template from the specified file."""
    try:
        prompt_path = PROMPTS_DIR / filename
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt {filename}: {e}")
        raise


enhancer_template_str = load_prompt("blackstone_enhancer_prompt.txt")
breakdown_template_str = load_prompt("blackstone_breakdown_prompt.txt")
data_sim_template_str = load_prompt("blackstone_data_simulator_prompt.txt")
synthesizer_template_str = load_prompt("blackstone_synthesizer_prompt.txt")

# --- Create Prompt Templates ---
enhancer_prompt = PromptTemplate(
    input_variables=["user_request"], template=enhancer_template_str
)
breakdown_prompt = PromptTemplate(
    input_variables=["enhanced_request"], template=breakdown_template_str
)
data_sim_prompt = PromptTemplate(
    input_variables=["enhanced_request", "data_task"], template=data_sim_template_str
)
synthesizer_prompt = PromptTemplate(
    input_variables=["enhanced_request", "simulated_data_results"],
    template=synthesizer_template_str
)

# --- Create Chains ---
# Use reasoning model for enhancement and breakdown (more complex tasks)
enhancer_chain = LLMChain(
    llm=llm_client.get_llm(model_type="reasoning"),  # Or choose specific model
    prompt=enhancer_prompt,
    output_key="enhanced_request"
)

breakdown_chain = LLMChain(
    llm=llm_client.get_llm(model_type="reasoning"),
    prompt=breakdown_prompt,
    output_key="data_tasks_str"  # Output will be a string list of tasks
)

# Use concept model for simulation and synthesis (more generative tasks)
data_sim_chain = LLMChain(
    llm=llm_client.get_llm(model_type="concept"),
    prompt=data_sim_prompt
    # Output key isn't fixed here as we call it in a loop
)

synthesizer_chain = LLMChain(
    llm=llm_client.get_llm(model_type="concept"),  # Or reasoning if complex synthesis needed
    prompt=synthesizer_prompt,
    output_key="final_summary"
)


# --- Workflow Function ---
def run_blackstone_workflow(user_request: str) -> dict:
    """
    Runs the Blackstone-style workflow: Enhance -> Breakdown -> Simulate -> Synthesize.
    """
    logger.info(f"Starting Blackstone workflow for request: {user_request!r}")
    full_results = {"initial_request": user_request}

    try:
        # 1. Enhance Prompt
        logger.info("Step 1: Enhancing prompt...")
        enhancer_result = enhancer_chain.invoke({"user_request": user_request})
        enhanced_request = enhancer_result.get("enhanced_request", "").strip()
        if not enhanced_request:
            raise ValueError("Prompt enhancement failed.")
        full_results["enhanced_request"] = enhanced_request
        logger.info(f"Enhanced Request: {enhanced_request}")

        # 2. Breakdown Task
        logger.info("Step 2: Breaking down enhanced request into data tasks...")
        breakdown_result = breakdown_chain.invoke({"enhanced_request": enhanced_request})
        data_tasks_str = breakdown_result.get("data_tasks_str", "").strip()
        if not data_tasks_str:
            raise ValueError("Task breakdown failed.")
        full_results["data_tasks_list_str"] = data_tasks_str
        logger.info(f"Data Tasks Identified (raw):\n{data_tasks_str}")

        # Simple parsing of numbered list (adjust regex if format differs)
        # This regex looks for lines starting with a number and a dot/parenthesis.
        tasks = re.findall(r"^\s*\d+[.)]?\s*(.*)", data_tasks_str, re.MULTILINE)
        if not tasks:
            logger.warning("Could not parse tasks from breakdown string, treating as one task.")
            tasks = [data_tasks_str]  # Fallback: treat the whole string as one task
        full_results["parsed_tasks"] = tasks
        logger.info(f"Parsed {len(tasks)} tasks.")

        # 3. Simulate Data Gathering (Loop)
        logger.info(f"Step 3: Simulating data gathering for {len(tasks)} tasks...")
        simulated_data = []
        for i, task in enumerate(tasks):
            task = task.strip()
            if not task: continue
            logger.debug(f"  Simulating task {i + 1}/{len(tasks)}: {task}")
            try:
                sim_result = data_sim_chain.invoke({
                    "enhanced_request": enhanced_request,
                    "data_task": task
                })
                # LLMChain returns dict, get the text output (Langchain updates changed this)
                sim_output = sim_result.get(data_sim_chain.output_key, "Simulation failed")
                simulated_data.append(f"--- Task: {task}\nResult:\n{sim_output.strip()}\n---")
                logger.debug(f"  Simulation result: {sim_output.strip()}")
            except Exception as sim_e:
                logger.error(f"Error simulating data for task '{task}': {sim_e}")
                simulated_data.append(f"--- Task: {task}\nResult: Error during simulation ---\n")

        full_results["simulated_data_outputs"] = simulated_data
        simulated_data_results_str = "\n".join(simulated_data)
        logger.info("Data simulation complete.")
        logger.debug(f"Combined Simulated Data:\n{simulated_data_results_str}")

        # 4. Synthesize Results
        logger.info("Step 4: Synthesizing final summary...")
        if not simulated_data_results_str:
            simulated_data_results_str = "No data could be simulated."

        synthesizer_result = synthesizer_chain.invoke({
            "enhanced_request": enhanced_request,
            "simulated_data_results": simulated_data_results_str
        })
        final_summary = synthesizer_result.get("final_summary", "").strip()
        if not final_summary:
            raise ValueError("Final synthesis failed.")
        full_results["final_summary"] = final_summary
        logger.info(f"Final Summary:\n{final_summary}")

        logger.info("Blackstone workflow finished successfully.")
        return full_results

    except Exception as e:
        logger.error(f"Blackstone workflow failed: {e}", exc_info=True)
        full_results["error"] = str(e)
        return full_results


# --- Entry Point ---
if __name__ == '__main__':
    # Configure logging for detailed output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Example usage:
    initial_prompt = "Show portfolio-wide IRR by asset class and region YTD."
    # initial_prompt = "What's the exposure to the tech sector across Fund III and Fund IV?"
    # initial_prompt = "Summarize recent performance of our European real estate assets."

    results = run_blackstone_workflow(initial_prompt)

    # --- Formatted Output ---
    box_width = 100
    separator = "-" * box_width

    print("\n\n" + "=" * box_width)
    print(" B L A C K S T O N E   W O R K F L O W   R E S U L T S")
    print("=" * box_width)

    print(f"\n[ 1. Initial User Request ]")
    print(separator)
    print(results.get('initial_request', 'N/A'))

    print(f"\n[ 2. Enhanced CIO Request ]")
    print(separator)
    print(results.get('enhanced_request', '--- Enhancement Failed ---'))

    print(f"\n[ 3. Identified Data Tasks ]")
    print(separator)
    print(results.get('data_tasks_list_str', '--- Breakdown Failed ---'))  # Show raw breakdown list

    print(f"\n[ 4. Simulated Data Gathering Results ]")
    print(separator)
    if 'simulated_data_outputs' in results:
        # Print each simulated result clearly
        for item in results['simulated_data_outputs']:
            print(item)
            print("-" * (box_width // 2))  # Small separator between items
    else:
        print("--- Simulation Failed or Skipped ---")

    print(f"\n[ 5. Final Synthesized Summary for CIO ]")
    print(separator)
    print(results.get('final_summary', '--- Synthesis Failed ---'))

    if 'error' in results:
        print(f"\n[ WORKFLOW ERROR ]")
        print(separator)
        print(results['error'])

    print("\n" + "=" * box_width)
    print(" E N D   O F   W O R K F L O W   R E S U L T S")
    print("=" * box_width + "\n")
