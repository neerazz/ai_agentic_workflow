# --- START OF FILE deepseek_ollama_client.py ---

import logging

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)


class DeepseekOllamaClient:
    """
    Wrapper for models running locally via Ollama (like Deepseek),
    maintaining a structure similar to other dual-model clients.
    Allows specifying different Ollama models for 'reasoning' and 'concept' tasks.
    """

    def __init__(self,
                 reasoning_model: str = "deepseek-coder:latest",  # Example: Use coder for reasoning
                 concept_model: str = "deepseek-llm:latest",  # Example: Use base llm for concepts
                 default_model_type: str = "reasoning",  # 'reasoning' or 'concept'
                 ollama_base_url: str = "http://localhost:11434",  # Default Ollama URL
                 verbose: bool = False):
        """
        Initializes the Ollama client wrapper.

        Args:
            reasoning_model: The name of the Ollama model to use for 'reasoning' tasks
                             (Make sure you have run `ollama pull <model_name>`).
            concept_model: The name of the Ollama model to use for 'concept' tasks
                           (Make sure you have run `ollama pull <model_name>`).
            default_model_type: Which model type ('reasoning' or 'concept') to use by default.
            ollama_base_url: The base URL for your Ollama instance.
            verbose: Set Langchain verbosity for the Ollama models.
        """
        logger.info(
            "Initializing DeepseekOllamaClient (reasoning_model=%s, concept_model=%s, default_model_type=%s, base_url=%s)",
            reasoning_model, concept_model, default_model_type, ollama_base_url
        )

        if default_model_type not in ["reasoning", "concept"]:
            raise ValueError("default_model_type must be 'reasoning' or 'concept'")

        # No API Key needed for local Ollama connection

        self.reasoning_model_name = reasoning_model
        self.concept_model_name = concept_model
        self.ollama_base_url = ollama_base_url
        self.default_model_type = default_model_type

        try:
            # Initialize LLMs using ChatOllama
            self.reasoning_llm = ChatOllama(
                model=self.reasoning_model_name,
                base_url=self.ollama_base_url,
                verbose=verbose
                # You can add other ChatOllama parameters like temperature, top_p, etc. here
                # temperature=0.7
            )
            logger.info(f"Successfully initialized reasoning model '{self.reasoning_model_name}' via Ollama.")

            self.concept_llm = ChatOllama(
                model=self.concept_model_name,
                base_url=self.ollama_base_url,
                verbose=verbose
                # temperature=0.8
            )
            logger.info(f"Successfully initialized concept model '{self.concept_model_name}' via Ollama.")

        except Exception as e:
            logger.error(f"Failed to initialize Ollama models. Ensure Ollama is running and models are pulled.",
                         exc_info=True)
            logger.error(f"Error details: {e}")
            # Depending on requirements, you might want to raise the exception
            # or allow the object to be created in a non-functional state.
            raise RuntimeError(f"Ollama initialization failed: {e}") from e

    def get_llm(self, model_type: str = None) -> ChatOllama:
        """
        Returns the appropriate ChatOllama instance based on the requested type or default.

        Args:
            model_type: 'reasoning', 'concept', or None (to use default).

        Returns:
            The corresponding ChatOllama instance.
        """
        chosen_type = model_type or self.default_model_type
        if chosen_type == "concept":
            llm = self.concept_llm
            model_name = self.concept_model_name
        else:  # Default to reasoning
            llm = self.reasoning_llm
            model_name = self.reasoning_model_name

        logger.debug("get_llm(model_type=%s) -> selected type '%s' (model: %s)", model_type, chosen_type, model_name)
        return llm

    def __call__(self, prompt: str, model_type: str = None) -> str:
        """
        Invokes the specified or default Ollama model with the given prompt.

        Args:
            prompt: The input prompt string.
            model_type: 'reasoning', 'concept', or None (to use default).

        Returns:
            The string content of the model's response. Returns empty string on error.
        """
        chosen_type = model_type or self.default_model_type
        selected_llm = self.get_llm(model_type)
        model_name = selected_llm.model  # Get model name from the instance

        logger.info("Calling Ollama (type: %s, model: %s)... Prompt: %s",
                    chosen_type, model_name, prompt[:150] + ("..." if len(prompt) > 150 else ""))

        try:
            # Invoke the selected LLM
            response = selected_llm.invoke(prompt)

            # Extract the text content from the response object (typically AIMessage)
            if isinstance(response, AIMessage) and hasattr(response, 'content'):
                response_content = response.content
                logger.debug("Ollama response received successfully.")
                return response_content
            else:
                # Fallback in case the response structure is different or not AIMessage
                logger.warning(
                    "Ollama response object was not AIMessage or did not have 'content' attribute. Returning raw string response.")
                return str(response)

        except Exception as e:
            logger.error(f"Error invoking Ollama model '{model_name}': {e}", exc_info=True)
            return f"Error: Could not get response from Ollama model '{model_name}'."


# --- Example Usage (Optional) ---
if __name__ == '__main__':

    try:
        # Ensure Ollama is running and you have pulled the models:
        # ollama pull deepseek-coder:latest
        # ollama pull deepseek-llm:latest
        print("Attempting to initialize DeepseekOllamaClient...")
        ollama_client = DeepseekOllamaClient(
            reasoning_model="deepseek-coder:latest",
            concept_model="deepseek-llm:latest",
            default_model_type="reasoning",  # Or "concept"
            verbose=False  # Set to True for more Langchain output
        )
        print("Client initialized successfully.")

        # --- Test Reasoning Model ---
        print("\nTesting Reasoning Model ('deepseek-coder')...")
        reasoning_prompt = "Write a python function to calculate the factorial of a number."
        reasoning_response = ollama_client(reasoning_prompt, model_type="reasoning")  # Explicitly choose
        # Or use default: reasoning_response = ollama_client(reasoning_prompt)
        print(f"\nPrompt:\n{reasoning_prompt}")
        print(f"\nReasoning Response:\n{reasoning_response}")

        print("\n" + "-" * 50 + "\n")

        # --- Test Concept Model ---
        print("Testing Concept Model ('deepseek-llm')...")
        concept_prompt = "Explain the concept of recursion in simple terms."
        concept_response = ollama_client(concept_prompt, model_type="concept")  # Explicitly choose
        print(f"\nPrompt:\n{concept_prompt}")
        print(f"\nConcept Response:\n{concept_response}")

        print("\n" + "-" * 50 + "\n")
        print("Testing complete.")

    except Exception as e:
        print(f"\n--- An error occurred during testing ---")
        print(e)
        print(
            "Please ensure Ollama is running and the specified models ('deepseek-coder:latest', 'deepseek-llm:latest') have been pulled.")
        print("You can pull models using: `ollama pull <model_name>`")
