import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from src.ai_agentic_workflow.utils.env_reader import get_env_variable

# Ensure logging is configured for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Start of DualModelGeminiClient (Copied from your provided immersive for self-containment) ---
class DualModelGeminiClient:
    """
    Wrapper for Gemini that maintains reasoning and concept LLMs with facade.
    """

    def __init__(self,
                 reasoning_model: str = "gemini-1.5-flash",
                 concept_model: str = "gemini-1.5-flash",
                 default_model: str = "reasoning"):
        logger.info(
            "Initializing DualModelGeminiClient (reasoning_model=%s, concept_model=%s, default_model=%s)",
            reasoning_model, concept_model, default_model
        )

        api_key = get_env_variable("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not found. Gemini client might fail to authenticate.")
            raise ValueError("GEMINI_API_KEY is not set. Please set it in your environment variables.")

        self.reasoning_llm = ChatGoogleGenerativeAI(google_api_key=api_key, model=reasoning_model)
        self.concept_llm = ChatGoogleGenerativeAI(google_api_key=api_key, model=concept_model)
        self.default_model = default_model
        logger.debug(
            f"Gemini clients initialized: reasoning_llm model='{reasoning_model}', concept_llm model='{concept_model}'")

    def get_llm(self, model_type: str = None):
        chosen = model_type or self.default_model
        llm = self.concept_llm if chosen == "concept" else self.reasoning_llm
        logger.debug(f"get_llm: requested model_type='{model_type}', chosen='{chosen}'")
        return llm

    def __call__(self, prompt: str, model_type: str = None) -> str:
        chosen = model_type or self.default_model
        logger.info(
            "GeminiClient __call__ (model_type=%s): prompt=%s",
            chosen, prompt[:100]  # Log first 100 chars of prompt
        )
        return self.get_llm(model_type).invoke(prompt)


# --- End of DualModelGeminiClient ---

if __name__ == "__main__":
    # IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual Google Gemini API Key.
    # Alternatively, ensure GEMINI_API_KEY is set as an environment variable
    # before running this script (e.g., in your shell: export GEMINI_API_KEY='your_key').
    # For this example to be self-contained and run directly, we'll set it here.
    # In a real application, reading from env_reader is preferred.
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

    if os.environ["GEMINI_API_KEY"] == "YOUR_GEMINI_API_KEY" or not os.environ["GEMINI_API_KEY"]:
        print(
            "WARNING: Please set your GEMINI_API_KEY environment variable or replace 'YOUR_GEMINI_API_KEY' in the script.")
        print("Exiting test as API key is not configured.")
    else:
        try:
            print("\n" + "=" * 50)
            print("  STARTING GEMINI CLIENT TEST")
            print("=" * 50 + "\n")

            # Initialize the Gemini client
            print("Attempting to initialize DualModelGeminiClient...")
            gemini_client = DualModelGeminiClient(
                reasoning_model="gemini-1.5-flash",  # Ensure this model is available to you
                concept_model="gemini-1.5-flash",  # Ensure this model is available to you
                default_model="reasoning"
            )
            print("DualModelGeminiClient initialized successfully.\n")

            # Test a simple prompt with the reasoning model
            test_prompt_reasoning = "What is the capital of France?"
            print(f"Sending prompt to reasoning model: '{test_prompt_reasoning}'")
            response_reasoning = gemini_client(test_prompt_reasoning, model_type="reasoning")

            print("\n--- Response from Reasoning Model (Text Content Only) ---")
            print(response_reasoning.content)  # Accessing the content attribute
            print("\n")  # Add a blank line for separation

            # Test a simple prompt with the concept model (if different or for specific use)
            test_prompt_concept = "Explain the concept of recursion in one sentence."
            print(f"Sending prompt to concept model: '{test_prompt_concept}'")
            response_concept = gemini_client(test_prompt_concept, model_type="concept")

            print("\n--- Response from Concept Model (Text Content Only) ---")
            print(response_concept.content)  # Accessing the content attribute
            print("\n")  # Add a blank line for separation

            print("=" * 50)
            print("  GEMINI CLIENT TEST COMPLETED")
            print("=" * 50 + "\n")

        except ValueError as ve:
            print(f"\nConfiguration Error: {ve}")
        except Exception as e:
            print(f"\nAn unexpected error occurred during client test: {e}")
            logger.exception("Detailed error during Gemini client test:")
